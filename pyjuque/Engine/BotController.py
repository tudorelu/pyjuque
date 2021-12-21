from decimal import Decimal
from uuid import uuid4
import time
from pprint import pprint
from pyjuque.Engine.Models import TABotModel as Bot, PairModel as Pair, OrderModel as Order
from pyjuque.Engine.OrderManager import placeNewOrder, simulateOrderInfo, cancelOrder
from traceback import format_exc
import sys

# from ccxt.base.errors import (AuthenticationError, BadRequest, BadResponse, 
#     BadSymbol, DuplicateOrderId, ExchangeError, OrderNotFound, InvalidOrder, 
#     InsufficientFunds, InvalidNonce, RateLimitExceeded, OnMaintenance, NetworkError, 
#     NotSupported, PermissionDenied, RequestTimeout, ArgumentsRequired, AccountSuspended, 
#     ExchangeNotAvailable)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotController:

    def __init__(self, session, bot, entry_settings, exit_settings, exchange, 
        strategy, timeframe = '5m', status_printer = None, logger_on = False):
        self.bot = bot
        self.session = session
        self.exchange = exchange
        self.strategy = strategy
        self.exit_settings = exit_settings
        self.entry_settings = entry_settings
        self.test_mode = bot.test_run
        self.timeframe = timeframe
        self.status_printer = status_printer
        self.logger_on = logger_on
        self.balances = dict()
        # Pre-calculate trading amounts
        self.total_amount = Decimal(self.bot.starting_balance)
        self.trade_amount = Decimal(self.entry_settings.trade_amount) 
        self.signal_distance = self.entry_settings.signal_distance
        self.long_signal_distance_multiplier = Decimal('1')
        self.short_signal_distance_multiplier = Decimal('1')
        if self.signal_distance != Decimal(0):
            self.long_signal_distance_multiplier = Decimal('0.01') * (Decimal('100') - self.signal_distance)
            self.short_signal_distance_multiplier = Decimal('0.01') * (Decimal('100') + self.signal_distance)
        if self.exit_settings.profit_target is not None:
            self.long_take_profit_multiplier = Decimal('0.01') * (Decimal('100') + Decimal(self.exit_settings.profit_target))
        if self.exit_settings.stop_loss_value is not None:
            self.stop_loss_multiplier = (Decimal('100') - Decimal(self.exit_settings.stop_loss_value)) * Decimal('0.01')

    
    def _updateBalances(self):
        balances = self.exchange.ccxt.fetchBalance()
        self.balances = balances

    def _getLatestCandles(self, symbol, timeframe):
        ''' Gets the latest data for this symbol on this exchange'''
        try:
            return self.exchange.getOHLCV(symbol=symbol, interval=timeframe, limit=self.strategy.minimum_period)
        except Exception:
            self.log(f'Error getting data from the exchange for {symbol}:')
            self.logError(format_exc())
            return None


    def executeBot(self):
        """ The main execution loop of the bot """
        if self.status_printer != None:
            self.status_printer.start()
        # Step 1: Retreive all pairs for a particular bot
        self.log("Getting active pairs:", should_print=False)
        all_pairs = self.bot_model.getPairs(self.session)
        active_pairs = self.bot_model.getActivePairs(self.session)
        self.log(f"Number of active_pairs: {len(active_pairs)}", should_print=False)
        # Step 2 For every pair:
        #	Retreive current market data
        self.log("Getting market data for all pairs...", should_print=False)
        self.latest_dfs = dict()
        for pair in all_pairs:
            df = self._getLatestCandles(pair.symbol, self.timeframe, self.strategy.minimum_period)
            self.latest_dfs[pair.symbol] = df
        # Step 3 For every active pair:
        # 	Compute indicators & check if strategy
        #		If strategy fulfilled, palce order & save order in DB
        self.log("Checking signals on active pairs...", should_print=False)
        for pair in active_pairs:
            self.log(f"Checking signal on {pair.symbol}", should_print=False)
            self.tryEntryOrder(pair)
        # Step 3: Retreive all open orders on the bot
        self.log("Getting open orders:", should_print=False)
        open_orders = self.bot_model.getOpenOrders(self.session)
        self.log(f"Number of open orders: {len(open_orders)}", should_print=False)
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


    def checkEntrySignal(self, symbol):
        """ Default function that checks up the entry strategy. 
            Can be overridden for custom strategies.
        """
        try:
            df = self.latest_dfs[symbol]
            if df == None:
                self.log(f'df for {symbol} is none')
                return False, None
        except Exception:
            self.log(f'Error getting data from the exchange for {symbol}:')
            self.logError(format_exc())
            return False, None
        try:
            self.strategy.setUp(df)
            entry_signal, last_price = self.strategy.checkLongSignal(len(df) - 1)
            if last_price == None:
                last_price = df.iloc[-1]['close']
        except Exception:
            self.log(f'Error computing indicators for {symbol}:')
            self.logError(format_exc())
            return False, None
        return entry_signal, last_price


    def tryEntryOrder(self, pair):
        """
        Gets the latest market data and runs the strategy off of it. 
        If strategy returns entry signal, entry is made.
        """
        entry_signal, last_price = self.checkEntrySignal(pair.symbol)
        if entry_signal:
            self.log(f'Got entry signal on {pair.symbol}.')
            side = 'buy'
            desired_price = None
            if self.signal_distance == Decimal(0):
                order_type = 'market'
            else:
                desired_price = Decimal(last_price) * self.long_signal_distance_multiplier
                order_type = 'limit'
            quantity = self.trade_amount / desired_price
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
                self.log(f'Not placing order on {pair.symbol} due to insuficient balance.')
            self.session.commit()


    def updateOpenOrder(self, order):
        """
        Checks the status of an open order and updates it
        """
        pair = self.bot_model.getPair(self.session, symbol=order.symbol)
        self.log(f'Checking open order on {order.symbol}.', should_print=False)
        # get info of order from exchange
        if not self.test_mode: 
            try:
                exchange_order_info = self.exchange.getOrder(order.symbol, order.id, is_custom_id=True)
            except Exception as e:
                self.log('Error getting data from the exchange for'
                    f' updating open order on {order.symbol}.')
                self.logError(sys.exc_info()[0])
                self.logError(sys.exc_info()[1])
                self.logError(sys.exc_info()[2])
                return
        else:
            try:
                exchange_order_info = simulateOrderInfo(self.exchange, order, self.timeframe)
            except Exception as e:
                self.log(f'Error simulating open order on {order.symbol}.')
                self.logError(sys.exc_info()[0])
                self.logError(sys.exc_info()[1])
                self.logError(sys.exc_info()[2])
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
                self.log(f'CANCELED BUY order on {order.symbol}, exiting remaining'
                    f' quantity: {order.executed_quantity} at market price.')
                self.instantlyExitOrder(order, pair)
                self.processClosedPosition(order, pair)
            # buy order was filled, place exit order.
            if (order.status == 'closed'):
                self.log(f'FILLED BUY order on {order.symbol}, try exit.')
                self.tryExitOrder(order, pair)
            # buy order has been accepted by engine
            if (order.status == 'open'):
                self.log(f'OPEN BUY order on {order.symbol}, UPDATING.')
                self.updateOpenBuyOrder(order, pair)
            # buy order was rejected, not processed by engine
            if (order.status == 'rejected'):
                self.log(f'REJECTED BUY order on {order.symbol}.')
                self.processClosedPosition(order, pair)
            # buy order expired, i.e. FOK orders with 
            # no fill or due to maintenance by exchange.
            if (order.status == 'expired'):
                self.log(f'EXPIRED BUY order on {order.symbol}, sell what was bought.')
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
                self.log(f'CANCELED SELL order on {order.symbol}')
                # self.instantlyExitOrder(order, pair)
                self.processClosedPosition(order, pair)
            # sell order was filled
            if (order.status == 'closed'):
                self.log(f'FILLED SELL order on {order.symbol}.')
                self.processClosedPosition(order, pair)
            # sell order was accepted by engine of exchange
            if (order.status == 'open'):
                self.log(f'OPEN SELL order on {order.symbol}, UPDATING.')
                try:
                    self.updateOpenSellOrder(order, pair)
                except:
                    self.logError('Error trying to update open sell order on '
                        f'{order.symbol} with id {order.id}')
            # sell order was rejected by engine of exchange
            if (order.status == 'rejected'):
                self.log(f'REJECTED SELL order on {order.symbol}.')
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
            # sell order expired, i.e. due to FOK orders or partially filled market orders
            if (order.status == 'expired'):
                self.log(f'EXPIRED SELL order on {order.symbol}.')
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)
        self.session.commit()


    def reviveOriginalBuyOrder(self, order):
        """ If sell order was cancelled due to some reason, revive buy 
            order and look to exit again. """
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
                    self.logError(f'cancelOrder() failed on {order.symbol}')
                    self.logError(format_exc())
                    return
            self.log(f'Canceled BUY order on {order.symbol} due to timeout.')
            # self.exchange.updateSQLOrderModel(order, order_result, None)
            self.processClosedPosition(order, pair)


    def updateOpenSellOrder(self, order, pair):
        """
        Update open sell order based on given params in exit settings.
        For now only supports placing stop loss market order when 
        position goes against us (basically simple oco order variant)
        """
        try:
            df = self.latest_dfs[order.symbol]
            if df == None:
                self.log(f'df for {order.symbol} is none.')
                return False, None
        except Exception:
            self.log('Error getting data from the exchange '
                f'for updating open sell order on {pair.symbol}:')
            self.logError(format_exc())
            return
        current_price = Decimal(df.iloc[-1]['close'])
        exit_signal, last_price = self.checkExitStrategy(order.symbol)
        side = 'sell'
        order_type = 'market'
        cancel_and_place_new_order = False
        if (self.bot_model.exit_settings.stop_loss_value != None \
            and (order.stop_price != None and order.stop_price > current_price)):
            cancel_and_place_new_order = True
            self.log('Cancelling existing sell order and placing '
                f'market sell on {order.symbol} due to stop loss.')
        elif (self.bot_model.exit_settings.exit_on_signal and exit_signal):
            cancel_and_place_new_order = True
            self.log('Cancelling existing sell order and placing '
                f'market sell on {order.symbol} due to exit signal.')
        elif (self.bot_model.exit_settings.profit_target != None):
            pt = self.bot_model.exit_settings.profit_target
            if order.price * Decimal((100 + pt) / 100) < current_price:
                cancel_and_place_new_order = True
                self.log('Cancelling existing sell order and placing '
                    f'market sell on {order.symbol} due to reaching profit target.')
        if cancel_and_place_new_order:
            quantity = self.computeMatchingOrderQuantity(order)
            if not self.test_mode:
                try:
                    cancelOrder(self.exchange, order)
                    if order.executed_quantity > 0:
                        self.bot_model.current_balance += order.executed_quantity * order.price
                except Exception:
                    self.log(f'cancelOrder() failed on {order.symbol}')
                    self.logError(format_exc())
                    return
            else:
                order_result = dict(status='canceled', filled = 0)
            # pprint(order_result)
            order.status = 'canceled' # order_result['status']
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
            df = self.latest_dfs[symbol]
            if df == None:
                self.log(f'df for {symbol} is none')
                return False, None
        except Exception:
            self.log(f'Error getting data from the exchange for {symbol}:')
            self.logError(format_exc())
            return False, None
        try:
            self.strategy.setUp(df)
            last_price = df.iloc[-1]['close']
            exit_signal = self.strategy.checkShortSignal(len(df) - 1)
        except Exception as e:
            self.log(f'Error computing indicators for {symbol}:')
            self.logError(format_exc())
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
            exit_signal, last_price = self.checkExitStrategy(order.symbol)
            place_trade = False
            if self.bot_model.exit_settings.exit_on_signal and exit_signal:
                order_type = 'market'
                side = 'sell'
                place_trade = True
            else:
                last_price = order.price
                stop_loss_value = self.bot_model.exit_settings.stop_loss_value 
                profit_target = self.bot_model.exit_settings.profit_target
                if stop_loss_value is not None:
                    price = Decimal(last_price) * Decimal((100 - stop_loss_value) / 100)
                    order_type = 'stop_loss'
                    side = 'sell'
                    place_trade = True
                elif profit_target is not None:
                    price = Decimal(last_price) * Decimal((100 + profit_target) / 100)
                    order_type = 'limit'
                    side = 'sell'
                    place_trade = True
                    # if stop_loss_value is not None:
                    #     stop_price = Decimal(last_price) * Decimal((100 - stop_loss_value) / 100)
            # If trade can go through
            if place_trade:
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
            self.bot_model.current_balance += order.executed_quantity * order.price


    def placeOrder(self, symbol, pair, order=None, **order_params):
        """ Create Order model and place order to exchange. """
        order_params['bot_id'] = self.bot_model.id
        new_order_model = None
        try:
            new_order_model = placeNewOrder(
                self.exchange, symbol, pair, order, self.bot_model.test_run, order_params)
        except Exception:
            self.log(f'Error placing order for {symbol}:')
            self.logError(format_exc())
        if new_order_model != None:
            self.syncModels(pair, order, new_order_model)
            self.session.add(new_order_model)
            self.log(f'{new_order_model.side} Order was placed succesfully on {symbol}')


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
                Decimal(self.bot_model.entry_settings.trade_amount) 
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
            exit_quantity = order.original_quantity - order.executed_quantity
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