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

    def __init__(self, session, bot_model, exchange, strategy, timeframe = '5m', status_printer = None, logger_on = False):
        self.bot_model = bot_model
        self.session = session
        self.exchange = exchange
        self.strategy = strategy
        self.test_mode = bot_model.test_run
        self.kline_interval = timeframe
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
        try:
            self.strategy.setUp(df)
            entry_signal = self.strategy.checkLongSignal(len(df) - 1)
            last_price = df.iloc[-1]['close']
        except Exception as e:
            self.log('Error computing indicators for {}:'.format(symbol))
            self.logError(sys.exc_info())
            return False, None
        return entry_signal, last_price


    def tryEntryOrder(self, pair):
        """
        Gets the latest market data and runs the strategy off of it. 
        If strategy returns entry signal, entry is made.
        """
        entry_signal, last_price = self.checkEntryStrategy(pair.symbol)
        if entry_signal:
            self.log('Got entry signal on {}.'.format(pair.symbol))
            side = 'buy'
            quote_qty = self.bot_model.starting_balance \
                * Decimal(self.bot_model.entry_settings.initial_entry_allocation) / 100
            desired_price = None
            if self.bot_model.entry_settings.signal_distance == 0:
                order_type = 'market'
            else:
                desired_price = Decimal(last_price) \
                    * Decimal((100 - self.bot_model.entry_settings.signal_distance) / 100 )
                order_type = 'limit'
            quantity = quote_qty / desired_price
            if self.bot_model.current_balance > 0:
                self.placeOrder(
                    symbol=pair.symbol, 
                    pair=pair, 
                    side=side, 
                    price=desired_price,  
                    quantity=quantity, 
                    order_type=order_type, 
                    is_entry=True)
            else:
                self.log('Not placing order on {} due to insuficient balance.'.format(pair.symbol))
            self.session.commit()


    def updateOpenOrder(self, order):
        """
        Checks the status of an open order and updates it
        """
        pair = self.bot_model.getPair(self.session, symbol=order.symbol)
        self.log('Checking open order on {}.'.format(order.symbol), should_print=False)
        # get info of order from exchange
        if not self.test_mode: 
            try:
                exchange_order_info = self.exchange.getOrder(order.symbol, order.id, is_custom_id=True)
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
        self.exchange.updateSQLOrderModel(order, exchange_order_info, None)
        self.session.commit()
        # update order params.
        # order.side = exchange_order_info['side']
        # order.status = exchange_order_info['status']
        # order.executed_quantity = exchange_order_info['filled']
        if (order.side == 'buy'):
            # Order has been canceled by the user
            if (order.status == 'canceled'):
                self.log('CANCELED BUY order on {}, exiting remaining quantity: {} at market price.'.format(order.symbol, order.executed_quantity))
                self.instantlyExitOrder(order, pair)
                self.processClosedPosition(order, pair)
            # buy order was filled, place exit order.
            if (order.status == 'closed'):
                self.log('FILLED BUY order on {}, try exit.'.format(order.symbol))
                self.tryExitOrder(order, pair)
            # buy order has been accepted by engine
            if (order.status == 'open'):
                self.log('OPEN BUY order on {}, UPDATING.'.format(order.symbol))
                self.updateOpenBuyOrder(order, pair)
            # buy order was rejected, not processed by engine
            if (order.status == 'rejected'):
                self.log('REJECTED BUY order on {}.'.format(order.symbol))
                self.processClosedPosition(order, pair)
            # buy order expired, i.e. FOK orders with 
            # no fill or due to maintenance by exchange.
            if (order.status == 'expired'):
                self.log('EXPIRED BUY order on {}, sell what was bought.'.format(order.symbol))
                self.instantlyExitOrder(order, pair)
                self.processClosedPosition(order, pair)
        # sell order 
        elif (order.side == 'sell'):
            # was cancelled by user.
            if (order.status == 'canceled'):
                # query buy order to again place a sell order for that buy order.
                # self.log('CANCELED SELL order on {}.'.format(order.symbol))
                # original_buy_order = self.reviveOriginalBuyOrder(order)
                # self.tryExitOrder(original_buy_order, pair)
                self.log('CANCELED SELL order on {}'.format(order.symbol))
                # self.instantlyExitOrder(order, pair)
                self.processClosedPosition(order, pair)
            # sell order was filled
            if (order.status == 'closed'):
                self.log('FILLED SELL order on {}.'.format(order.symbol))
                self.processClosedPosition(order, pair)
            # sell order was accepted by engine of exchange
            if (order.status == 'open'):
                self.log('OPEN SELL order on {}, UPDATING.'.format(order.symbol))
                self.updateOpenSellOrder(order, pair)
            # sell order was rejected by engine of exchange
            if (order.status == 'rejected'):
                self.log('REJECTED SELL order on {}.'.format(order.symbol))
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
            # sell order expired, i.e. due to FOK orders or partially filled market orders
            if (order.status == 'expired'):
                self.log('EXPIRED SELL order on {}.'.format(order.symbol))
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
        self.session.commit()


    def reviveOriginalBuyOrder(self, order):
        """ If sell order was cancelled due to some reason, revive buy order and look to exit again. """
        original_buy_order = self.session.query(Order).get(order.id)
        original_buy_order.is_closed = False
        original_buy_order.executed_quantity = order.original_quantity - order.executed_quantity
        return original_buy_order


    def updateOpenBuyOrder(self, order, pair):
        """
        Looks to close an open buy order based on strategy specified 
        in entry settings. For now you can only close orders based on 
        time passed.
        """
        # TODO: place a sell order to exit if holding any 
        # asset bought through this order.
        if (time.time() * 1000 - (order.timestamp).timestamp()) \
            > self.bot_model.entry_settings.open_buy_order_time_out:
            if not self.test_mode:
                try:
                    order_result = cancelOrder(self.exchange, order)
                    if order.executed_quantity > 0:
                        self.instantlyExitOrder(order, pair)
                        self.bot_model.current_balance += \
                            order.executed_quantity * order.price
                    else:
                        self.bot_model.current_balance += \
                            order.original_quantity * order.price
                except Exception as e:
                    self.log('cancelOrder() failed on {}'.format(order.symbol))
                    self.log(e)
                    return
                # try:
                #     order_result = self.exchange.getOrder(order.symbol, order.id, is_custom_id=True)
                # except Exception as e:
                #     self.log('getting order failed after canceling order on {}'.format(order.symbol))
                #     self.log(e)
                #     return
            self.log('Canceled BUY order on {} due to timeout.'.format(order.symbol))
            # self.exchange.updateSQLOrderModel(order, order_result, None)
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
        current_price = Decimal(candlestick_data.iloc[-1]['close'])
        stop_loss_value = self.bot_model.exit_settings.stop_loss_value

        exit_signal, last_price = self.checkExitStrategy(order.symbol)
        side = 'sell'
        order_type = 'market'
        if (stop_loss_value != None and (order.stop_price > current_price)) or \
            (self.bot_model.exit_settings.exit_on_signal and exit_signal):
            quantity = self.computeMatchingOrderQuantity(order)
            if not self.test_mode:
                try:
                    cancelOrder(self.exchange, order)
                    if order.executed_quantity > 0:
                        self.bot_model.current_balance += \
                            order.executed_quantity * order.price
                except Exception as e:
                    self.log('cancelOrder() failed on {}'.format(order.symbol))
                    self.log(e)
                    return
                # try:
                #     order_result = self.exchange.getOrder(order.symbol, order.id, is_custom_id=True)
                # except Exception as e:
                #     self.log('getting order failed after canceling order')
                #     self.log(e)
                #     return
            else:
                order_result = dict(status='canceled', filled=0)

            if (stop_loss_value != None and (order.stop_price > current_price)):
                self.log('Canceling existing sell order and placing market sell on {} due to stop loss.'.format(order.symbol))
            elif (self.bot_model.exit_settings.exit_on_signal and exit_signal):
                self.log('Canceling existing sell order and placing market sell on {} due to exit signal.'.format(order.symbol))
            else:
                self.log('Canceling existing sell order and placing market sell on {} ...'.format(order.symbol))
            # pprint(order_result)
            order.status = 'canceled' #order_result['status']
            # order.executed_quantity = order_result['filled']
            order.is_closed = True
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
        try:
            self.strategy.setUp(df)
            exit_signal = self.strategy.checkShortSignal(len(df) - 1)
            last_price = df.iloc[-1]['close']
        except Exception as e:
            self.log('Error computing indicators for {}:'.format(symbol))
            self.logError(sys.exc_info())
            return False, None
        return exit_signal, last_price


    def tryExitOrder(self, order, pair):
        """ If strategy returns exit signal look to place exit order. """
        # Calculates quantity of order. 
        # Takes in to account partially filled orders.
        quantity = self.computeMatchingOrderQuantity(order)
        if quantity > 0:
            price = None
            stop_price = None
            # exit_signal, last_price = self.checkExitStrategy(order.symbol)
            # if self.bot_model.exit_settings.exit_on_signal and exit_signal:
            #     order_type = 'market'
            #     side = 'sell'
            # else:
            last_price = order.price
            stop_loss_value = self.bot_model.exit_settings.stop_loss_value 
            profit_target = self.bot_model.exit_settings.profit_target
            if profit_target is not None:
                price = Decimal(last_price) * Decimal((100 + profit_target) / 100)
                order_type = 'limit'
                side = 'sell'
                if stop_loss_value is not None:
                    stop_price = Decimal(last_price) * Decimal((100 - stop_loss_value) / 100)
            elif stop_loss_value is not None:
                price = Decimal(last_price) * Decimal((100 - stop_loss_value) / 100)
                order_type = 'stop_loss'
                side = 'sell'
            self.placeOrder(
                symbol=order.symbol, 
                pair=pair, 
                order=order, 
                price=price,
                entry_price=order.price, 
                stop_price=stop_price,
                quantity=quantity, 
                side=side, 
                order_type=order_type)


    def instantlyExitOrder(self, order, pair):
        """ If strategy returns exit signal look to place exit order. """
        quantity = self.computeMatchingOrderQuantity(order)
        order_type = 'market'
        side = 'buy'
        if order.side == 'buy':
            side = 'sell'
        if quantity > 0:
            self.placeOrder(
                symbol=order.symbol, 
                pair=pair, 
                order=order,
                quantity=quantity, 
                side=side, 
                order_type=order_type)


    def processClosedPosition(self, order, pair):
        """ Update status of closed position """
        order.is_closed = True
        pair.active = True
        pair.current_order_id = None
        if order.side == 'sell':
            self.bot_model.current_balance += \
                order.executed_quantity * order.price


    def placeOrder(self, symbol, pair, order=None, **order_params):
        """ Create Order model and place order to exchange. """
        order_params['bot_id'] = self.bot_model.id
        new_order_model = None
        try:
            new_order_model = placeNewOrder(
                self.exchange, symbol, pair, order, self.bot_model.test_run, order_params)
        except Exception as e:
            self.log('Error placing order for {}:'.format(symbol))
            self.logError(sys.exc_info())
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
            self.bot_model.current_balance -= \
                Decimal(self.bot_model.entry_settings.initial_entry_allocation) \
                    * self.bot_model.starting_balance / Decimal(100)
            pair.active = False
            pair.current_order_id = new_order_model.id

    # Keep Bot Balance Updated
    # Exit on Signal
    # Activate Simulation Mode

    def computeMatchingOrderQuantity(self, order):
        """ Compute exit quantity so that also partially 
        filled orders can be handled."""
        if order.side == 'buy':
            exit_quantity = order.executed_quantity
        elif order.side == 'sell':
            exit_quantity = order.original_quantity \
                - order.executed_quantity
        return exit_quantity


    def log(self, message, should_print=True, force=True):
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