from decimal import Decimal
from uuid import uuid4
import time
import math
from pprint import pprint
from pyjuque.Engine.Models import TABotModel as Bot, PairModel as Pair, OrderModel as Order
from pyjuque.Engine.OrderManager import placeNewOrder, simulateOrderInfo, cancelOrder
from pyjuque.Exchanges.Base.Exceptions import InvalidCredentialsException, \
    InternalExchangeException, ExchangeConnectionException
from traceback import print_exc
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import sys

class BotController:

    def __init__(self, session, bot_model, exchange, strategy, status_printer = None, logger_on = False):
        self.bot_model = bot_model
        self.session = session
        self.exchange = exchange
        self.strategy = strategy
        self.test_mode = bot_model.test_run
        self.kline_interval = '5m'
        self.status_printer = status_printer
        self.logger_on = logger_on


    def executeBot(self):
        """ The main execution loop of the bot """
        if self.status_printer != None:
            self.status_printer.start()
        # Step 1: Retreive all pairs for a particular bot
        self.log("Getting active pairs:", should_print=False)
        active_pairs = self.bot_model.getActivePairs(self.session)
        self.log("Number of active_pairs: {}".format(
                len(active_pairs)), should_print=False)
        # Step 2 For each pair:
        #	Retreive current market data
        # 	Compute indicators & check if strategy
        #		If strategy fulfilled, palce order & save order in DB
        self.log("Checking signals on pairs...", should_print=False)
        for pair in active_pairs:
            self.log("Checking signal on {}".format(pair.symbol), should_print=False)
            self.tryEntryOrder(pair)
        # Step 3: Retreive all open orders on the bot
        self.log("Getting open orders:", should_print=False)
        open_orders = self.bot_model.getOpenOrders(self.session)
        self.log("Number of open orders: {}".format(len(open_orders)), should_print=False)
        # Step 4: For Each order that was already placed by the bot
        # and was not filled before, check status:
        #       IF Filled 
        #           -> If entry order, place exit order
        #           -> If exit order, success (take profit), 
        #           or failure (stop loss): Resume trading!
        self.log("Checking orders state...", should_print=False)
        for order in open_orders:
            self.updateOpenOrder(order)
        
        self.log("Executed the bot loop. Now waiting...", should_print=False)


    def checkEntryStrategy(self, symbol):
        """ Default function that checks up the entry strategy. 
        Can be overridden for custom strategies.
        """
        try:
            df = self.exchange.getOHLCV(symbol, self.kline_interval, self.strategy.minimum_period)
        except Exception as e:
            self.log('Error getting data from the exchange for {}:'.format(symbol))
            self.logError(sys.exc_info())
            return False, None
        self.strategy.setUp(df)
        entry_signal = self.strategy.checkLongSignal(len(df) - 1)
        last_price = df.iloc[-1]['close']
        return entry_signal, last_price


    def tryEntryOrder(self, pair):
        """
        Gets the latest market data and runs the strategy off of it. 
        If strategy returns entry signal, entry is made.
        """
        entry_signal, last_price = self.checkEntryStrategy(pair.symbol)
        if entry_signal:
            side = 'buy'
            quote_qty = Decimal(self.bot_model.starting_balance) \
                * Decimal(self.bot_model.entry_settings.initial_entry_allocation) / 100
            if self.bot_model.entry_settings.signal_distance == 0:
                desired_price = Decimal(last_price)
                quantity = quote_qty / desired_price
                self.placeOrder(
                    symbol=pair.symbol, 
                    pair=pair, 
                    quantity=quantity, 
                    side=side, 
                    order_type='market', 
                    is_entry=True)
            else:
                desired_price = Decimal(last_price) \
                    * Decimal((100 - self.bot_model.entry_settings.signal_distance) / 100 )
                quantity = quote_qty / desired_price
                self.placeOrder(
                    symbol=pair.symbol, 
                    pair=pair, 
                    side=side, 
                    price=desired_price,  
                    quantity=quantity, 
                    order_type='limit', 
                    is_entry=True)
            self.session.commit()


    def updateOpenOrder(self, order):
        """
        Checks the status of an open order and updates it
        """
        pair = self.bot_model.getPairWithSymbol(self.session, order.symbol)
        self.log('Checking open order on {}.'.format(order.symbol), should_print=False)
        # get info of order from exchange
        if not self.test_mode: 
            try:
                exchange_order_info = self.exchange.getOrder(
                    order.symbol, order.id, is_custom_id=True)
            except Exception as e:
                self.log('Error getting data from the exchange for'
                    ' updating open order on {}.'.format(order.symbol))
                self.logError(sys.exc_info())
                return
        else:
            try:
                exchange_order_info = simulateOrderInfo(self.exchange, order, self.kline_interval)
            except Exception as e:
                self.log('Error simulating open order on {}.'.format(order.symbol))
                self.logError(sys.exc_info())
                return
        # update order params.
        order.side = exchange_order_info['side']
        order.status = exchange_order_info['status']
        order.executed_quantity = exchange_order_info['filled']
        if (order.side == 'buy'):
            # Order has been canceled by the user
            if (order.status == 'canceled'):
                if order.executed_quantity > 0:
                    self.tryExitOrder(order, pair)
                else:
                    self.processClosedPosition(order, pair)
            # buy order was filled, place exit order.
            if (order.status == 'closed'):
                self.log('BUY order on {} filled, try exit.'.format(order.symbol))
                self.tryExitOrder(order, pair)
            # buy order has been accepted by engine
            if (order.status == 'open'):
                self.updateOpenBuyOrder(order, pair)
            # buy order was rejected, not processed by engine
            if (order.status == 'rejected'):
                self.processClosedPosition(order, pair)
            # buy order expired, i.e. FOK orders with 
            # no fill or due to maintenance by exchange.
            if (order.status == 'expired'):
                if order.executed_quantity > 0:
                    self.tryExitOrder(order, pair)
                else:
                    self.processClosedPosition(order, pair)
        # sell order 
        if (order.side == 'sell'):
            # was cancelled by user.
            if (order.status == 'canceled'):
                # query buy order to again place a sell order for that buy order.
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
            # sell order was filled
            if (order.status == 'closed'):
                self.processClosedPosition(order, pair)
            # sell order was accepted by engine of exchange
            if (order.status == 'open'):
                self.updateOpenSellOrder(order, pair)
            # sell order was rejected by engine of exchange
            if (order.status == 'rejected'):
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
            # sell order expired, i.e. due to FOK orders or partially filled market orders
            if (order.status == 'expired'):
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
        self.session.commit()


    def reviveOriginalBuyOrder(self, order):
        """ If sell order was cancelled due to some reason, revive buy order and look to exit again. """
        original_buy_order = self.session.query(Order).get(order.id)
        original_buy_order.is_closed = False
        original_buy_order.executed_quantity = Decimal(order.original_quantity) - Decimal(order.executed_quantity)
        return original_buy_order


    def updateOpenBuyOrder(self, order, pair):
        """
        Looks to close an open buy order based on strategy specified 
        in entry settings. For now you can only close orders based on 
        time passed.
        """
        # How can we guarantee timestamp of exchange is always in ms?
        if (time.time() * 1000 - (order.timestamp).timestamp()) \
            > self.bot_model.entry_settings.open_buy_order_time_out:
            if not self.test_mode:
                try:
                    order_result = cancelOrder(self.exchange, order)
                except Exception as e:
                    self.log('cancelOrder() failed')
                    self.log(e)
                    return
            order.status = 'canceled'
            self.processClosedPosition(order, pair)


    def updateOpenSellOrder(self, order, pair):
        """
        Update open sell order based on given params in exit settings.
        For now only supports placing stop loss market order when 
        position goes against us (basically simple oco order variant)
        """
        try:
            candlestick_data = self.exchange.getOHLCV(order.symbol, self.kline_interval)
        except Exception:
            self.log('Error getting data from the exchange '
                'for updating open sell order on {}:'.format(pair.symbol))
            self.logError(sys.exc_info())
            return
        current_price = candlestick_data.iloc[-1]['close']
        stop_loss_value = self.bot_model.exit_settings.stop_loss_value
        if stop_loss_value is not None:
            if (Decimal(100 - stop_loss_value) / Decimal(100)) \
                * Decimal(order.entry_price) >= Decimal(current_price):
                quantity = self.computeMatchingOrderQuantity(order)
                side = 'sell'
                order_type = 'market'
                if not self.test_mode:
                    try:
                        order_result = cancelOrder(self.exchange, order)
                    except Exception as e:
                        self.log('cancelOrder() failed')
                        self.log(e)
                        return
                else:
                    order_result = dict(status='canceled', filled=0)
                order.status = order_result['status']
                order.executed_quantity = order_result['filled']
                self.placeOrder(
                    symbol=order.symbol,
                    pair=pair,
                    order=order,
                    quantity=quantity,
                    order_type=order_type,
                    side=side)


    def checkExitStrategy(self, symbol):
        """  Default function that checks the exit strategy. 
        Can be overwritten for custom strategies.
        """
        try:
            df = self.exchange.getOHLCV(symbol, self.kline_interval, self.strategy.minimum_period)
        except Exception:
            self.log('Error getting data from the exchange for {}:'.format(symbol))
            self.logError(sys.exc_info())
            return False, None
        self.strategy.setUp(df)
        exit_signal = self.strategy.checkShortSignal(len(df) - 1)
        last_price = df.iloc[-1]['close']
        return exit_signal, last_price


    def tryExitOrder(self, order, pair):
        """ If strategy returns exit signal look to place exit order. """
        exit_signal, last_price = self.checkExitStrategy(order.symbol)
        if self.bot_model.exit_settings.exit_on_signal and exit_signal:
            quantity = self.computeMatchingOrderQuantity(order)
            order_type = 'market'
            side = 'sell'
            if quantity > 0:
                self.placeOrder(
                    order.symbol, pair,
                    order = order,
                    quantity = quantity,
                    side = side,
                    order_type = order_type)
        else:
            # Calculates quantity of order. 
            # Takes in to account partially filled orders.
            last_price = order.price
            stop_loss_value = self.bot_model.exit_settings.stop_loss_value 
            profit_target = self.bot_model.exit_settings.profit_target
            quantity = self.computeMatchingOrderQuantity(order)
            if profit_target is not None:
                price = (Decimal(100 + profit_target) \
                    / Decimal(100)) * Decimal(last_price)
                order_type = 'limit'
                side = 'sell'
            elif stop_loss_value is not None:
                price = (Decimal(100 - stop_loss_value) \
                    / Decimal(100)) * Decimal(last_price)
                order_type = 'stop_loss'
                side = 'sell'

            if quantity > 0:
                self.placeOrder(
                    symbol=order.symbol, pair=pair, 
                    order=order, price=price, 
                    quantity=quantity, side=side, 
                    order_type=order_type)


    def processClosedPosition(self, order, pair):
        """ Update status of closed position """
        order.is_closed = True
        pair.active = True
        pair.current_order_id = None


    def placeOrder(self, symbol, pair, order=None, **order_params):
        """ Create Order model and place order to exchange. """
        order_params['bot_id'] = self.bot_model.id
        new_order_model = placeNewOrder(
            self.exchange, symbol, pair, order, self.bot_model.test_run, order_params)
        if new_order_model != None:
            self.syncModels(pair, order, new_order_model)
            self.session.add(new_order_model)
            self.log('{} Order was placed succesfully on {}'.format(
                new_order_model.side, symbol))


    def syncModels(self, pair, order, new_order_model):
        """ Sync pairs and orders to new status """
        if order is not None:
            new_order_model.matched_order_id = order.id
            order.is_closed = True
            order.matched_order_id = new_order_model.id
            pair.active = False
            pair.current_order_id = new_order_model.id
        if order is None:
            self.bot_model.current_balance = self.bot_model.current_balance \
                - Decimal(self.bot_model.entry_settings.initial_entry_allocation) \
                    * Decimal(self.bot_model.starting_balance) / 100
            pair.active = False
            pair.current_order_id = new_order_model.id


    def computeMatchingOrderQuantity(self, order):
        """ Compute exit quantity so that also partially 
        filled orders can be handled."""
        if order.side == 'buy':
            exit_quantity = order.executed_quantity
        elif order.side == 'sell':
            exit_quantity = Decimal(order.original_quantity) \
                - Decimal(order.executed_quantity)
        return exit_quantity


    def log(self, message, should_print=True, force=False):
        if self.status_printer != None:
            self.status_printer.stop()
            if should_print:
                logger.info(message)
            else:
                self.status_printer.text = message
            self.status_printer.start()
        elif self.logger_on or force:
            logger.info(message)


    def logError(self, message):
        if self.status_printer != None:
            self.status_printer.stop()
            print(message)
            self.status_printer.start()
        else:
            print(message)