from decimal import Decimal
from uuid import uuid4
import os
import yaml
import time
import math
import glob, importlib
from pprint import pprint
from pyjuque.Engine.Models import Bot, Pair, Order
from pyjuque.Engine.OrderManager import placeNewOrder, simulateOrderInfo
from pyjuque.Exchanges.Base.Exceptions import \
    InvalidCredentialsException, \
    InternalExchangeException, \
    ExchangeConnectionException
from traceback import print_exc
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import sys

class BotInitializer:
    def getStrategies():
        # Import all strategies by name from folder 
        Strategies = {}
        __globals = globals()
        for path in glob.glob('pyjuque/Strategies/[!_]*.py'):
            path, file = os.path.split(path)
            mod_name = file[:-3]
            if mod_name != 'BaseStrategy':
                mod_path = path.replace("/", ".") +'.' + mod_name
                Strategies[mod_name] = getattr(importlib.import_module(mod_path), mod_name)
        return Strategies

    def getYamlConfig(bot_name = None):
        # Import bot templates 
        with open(r'bots_config.yml') as file:
            bots = yaml.load(file, Loader=yaml.FullLoader)['bots']
            if bot_name is not None:
                for bot_config in bots:
                    if bot_config['name'] == bot_name:
                        return bot_config
            return bots[0]

class BotController:

    def __init__(self, session, bot, exchange, strategy, sp = None, sp_on = False, logger_on = False):
        self.bot = bot
        self.session = session
        self.exchange = exchange
        self.strategy = strategy
        self.test_mode = bot.test_run
        self.kline_interval = '5m'
        self.sp = sp
        self.sp_on = sp_on
        self.logger_on = logger_on

    def executeBot(self):
        """ The main execution loop of the bot """

        # Step 1: Retreive all pairs for a particular bot

        self.logOrSp("Getting active pairs:")

        active_pairs = self.bot.getActivePairs(self.session)
        
        self.logOrSp("Number of active_pairs: {}".format(
                len(active_pairs)))

        # Step 2 For Each Pair:
        #		Retreive current market data
        # 	Compute Indicators & Check if Strategy is Fulfilled
        #		IF Fulfilled, palce order (Save order in DB)
        self.logOrSp("Checking signals on pairs...")
        for pair in active_pairs:
            self.logOrSp("Checking signal on {}".format(pair.symbol))
            self.tryEntryOrder(pair)

        # Step 3: Retreive all open orders on the bot
        self.logOrSp("Getting open orders:")
        open_orders = self.bot.getOpenOrders(self.session)
        self.logOrSp("Number of open orders: {}".format(len(open_orders)))
        

        # Step 4: For Each order that was already placed by the bot
        # and was not filled before, check status:
        #       IF Filled 
        #           -> If entry order, place exit order
        #           -> If exit order, success (take profit), 
        #           or failure (stop loss): Resume trading!
        self.logOrSp("Checking orders state...")
        for order in open_orders:
            self.updateOpenOrder(order)

    def tryEntryOrder(self, pair):
        """
        Gets the latest market data and runs the strategy off of it. 
        If strategy returns entry signal, entry is made.
        """
        bot = self.bot
        exchange = self.exchange
        strategy = self.strategy

        symbol = pair.symbol

        try:
            df = exchange.getSymbolKlines(
                symbol, self.kline_interval, limit=strategy.minimum_period)
        except ExchangeConnectionException:
            self.logOrSp('Error getting data from the exchange for {}:'.format(symbol), should_print=True)
            self.logOrSp(sys.exc_info(), should_print=True)
            return
            
        strategy.setUp(df)
        i = len(df)-1

        # TODO It only works for LONG bots for now, 
        # but make it work for both long and short
        entry_signal = strategy.checkLongSignal(i)

        if entry_signal:
            side = 'BUY'
            quote_qty = Decimal(bot.starting_balance) \
                * Decimal(bot.entry_settings.initial_entry_allocation) / 100
            if bot.entry_settings.signal_distance == 0:
                desired_price = Decimal(df.iloc[-1]['close'])
                quantity = quote_qty / desired_price
                self.placeOrder(
                    symbol=symbol, pair=pair, quantity=quantity, 
                    side=side, order_type=exchange.ORDER_TYPE_MARKET, is_entry=True)
            else:
                desired_price = Decimal(df.iloc[-1]['close']) \
                    * Decimal((100 - bot.entry_settings.signal_distance) / 100 )
                quantity = quote_qty / desired_price
                price = desired_price
                self.placeOrder(
                    symbol=symbol, pair=pair, price=price, quantity=quantity, 
                    side=side, order_type=exchange.ORDER_TYPE_LIMIT, is_entry=True)

            self.session.commit()

    def updateOpenOrder(self, order):
        """
        Checks the status of an open order and updates it
        """
        exchange = self.exchange

        # get pair from database
        pair:Pair = self.bot.getPairWithSymbol(self.session, order.symbol)

        self.logOrSp('Checking open order on {}.'.format(pair.symbol))
        # get info of order from exchange
        if not self.test_mode: 
            try:
                exchange_order_info = exchange.getOrder(order.symbol, order.id, is_custom_id=True)
                print(exchange_order_info)
            except ExchangeConnectionException:
                self.logOrSp('Error getting data from the exchange for updating open order on {}.'.format(pair.symbol), should_print=True)
                self.logOrSp(sys.exc_info(), should_print=True)
                return
        else:
            try:
                exchange_order_info = simulateOrderInfo(exchange, order, self.kline_interval)
            except ExchangeConnectionException:
                self.logOrSp('Error simulating open order on {}.'.format(pair.symbol), should_print=True)
                self.logOrSp(sys.exc_info(), should_print=True)
                return
        # check for valid response from exchange
        if not exchange.isValidResponse(exchange_order_info):
            logger.warning('Exchange order info could not be retrieved!, \
                message from exchange: {}'.format(exchange_order_info))
            return
        
        # update order params.
        order.side = exchange_order_info['side']
        order.status = exchange_order_info['status']
        order.executed_quantity = exchange_order_info['executedQty']

        if (order.side == exchange.ORDER_SIDE_BUY):
             # Order has been canceled by the user
            if (order.status == exchange.ORDER_STATUS_CANCELED):
                if order.executed_quantity > 0:
                    self.tryExitOrder(order, pair)
                else:
                    self.processClosedPosition(order, pair)

            # buy order was filled, place exit order.
            if (order.status == exchange.ORDER_STATUS_FILLED):
                self.logOrSp('BUY order on {} filled, try exit.'.format(pair.symbol), should_print=True)

                self.tryExitOrder(order, pair)

            # buy order has been accepted by engine
            if (order.status == exchange.ORDER_STATUS_NEW):
                self.updateOpenBuyOrder(order, pair)

            # buy order that has been partially filled
            if (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
                self.updateOpenBuyOrder(order, pair)

            # buy order was rejected, not processed by engine
            if (order.status == exchange.ORDER_STATUS_REJECTED):
                self.processClosedPosition(order, pair)

            # buy order expired, i.e. FOK orders with 
            # no fill or due to maintenance by exchange.
            if (order.status == exchange.ORDER_STATUS_EXPIRED):
                if order.executed_quantity > 0:
                    self.tryExitOrder(order, pair)
                else:
                    self.processClosedPosition(order, pair)

        # sell order 
        if (order.side == exchange.ORDER_SIDE_SELL):
            # was cancelled by user.
            if (order.status == exchange.ORDER_STATUS_CANCELED):
                # query buy order to again place a sell order for that buy order.
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)

            # sell order was filled
            if (order.status == exchange.ORDER_STATUS_FILLED):
                self.processClosedPosition(order, pair)

            # sell order was accepted by engine of exchange
            if (order.status == exchange.ORDER_STATUS_NEW):
                self.updateOpenSellOrder(order, pair)

            # sell order was partially filled
            if (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
                self.updateOpenSellOrder(order, pair)

            # sell order was rejected by engine of exchange
            if (order.status == exchange.ORDER_STATUS_REJECTED):
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)

            # sell order expired, i.e. due to FOK orders or partially filled market orders
            if (order.status == exchange.ORDER_STATUS_EXPIRED):
                original_buy_order = self.reviveOriginalBuyOrder(order)
                self.tryExitOrder(original_buy_order, pair)

        self.session.commit()

    def reviveOriginalBuyOrder(self, order):
        """ If sell order was cancelled due to some reason, revive buy order and look to exit again. """
        original_buy_order = self.bot.getOrder(order.position_id)
        original_buy_order.is_closed = False
        original_buy_order.executed_quantity = Decimal(order.original_quantity) - Decimal(order.executed_quantity)
        return original_buy_order

    def updateOpenBuyOrder(self, order, pair):
        """
        Looks to close an open buy order based on strategy specified 
        in entry settings. For now you can only close orders based on 
        time passed.
        """
        exchange = self.exchange

        # How can we guarantee timestamp of exchange is always in ms?
        if (time.time() * 1000 - (order.timestamp).timestamp()) \
            > self.bot.entry_settings.open_buy_order_time_out:
            if not self.test_mode:
                order_result = exchange.cancelOrder(order.symbol, order.id)
            else:
                order_result = dict(status=self.exchange.ORDER_STATUS_CANCELED)
            if exchange.isValidResponse(order_result):
                order.status = order_result['status']
                self.processClosedPosition(order, pair)

    def updateOpenSellOrder(self, order, pair):
        """
        Update open sell order based on given params in exit settings.
        For now only supports placing stop loss market order when 
        position goes against us (basically simple oco order variant)
        """
        exchange = self.exchange
        bot = self.bot
        strategy = self.strategy
        try:
            candlestick_data = exchange.getSymbolKlines(
                order.symbol, self.kline_interval, strategy.minimum_period)
        except ExchangeConnectionException:
            self.logOrSp('Error getting data from the exchange for updating open sell order on {}:'.format(pair.symbol), should_print=True)
            self.logOrSp(sys.exc_info(), should_print=True)
            return
        current_price = candlestick_data.iloc[-1]['close']
        stop_loss_value = bot.exit_settings.stop_loss_value

        if stop_loss_value is not None:
            if ((Decimal(100) - Decimal(stop_loss_value)) / Decimal(100)) \
                * Decimal(order.entry_price) >= Decimal(current_price):
                quantity = self.computeQuantity(order)
                side = exchange.ORDER_SIDE_SELL
                order_type = exchange.ORDER_TYPE_MARKET

                if not self.test_mode:
                    order_result = exchange.cancelOrder(order.symbol, order.id)
                else:
                    order_result = dict(
                        status=exchange.ORDER_STATUS_CANCELED, executedQty=0)

                if exchange.isValidResponse(order_result):
                    # TODO probably taking over info from exchange like
                    # this will not be modular enough for other exchanges.
                    order.status = order_result['status']
                    order.executed_quantity = order_result['executedQty']

                    self.placeOrder(
                        symbol=order.symbol,
                        pair=pair,
                        order=order,
                        quantity=quantity,
                        order_type=order_type,
                        side=side)

    def tryExitOrder(self, order, pair):
        """ If strategy returns exit signal look to place exit order. """
        bot = self.bot
        symbol = order.symbol
        exchange = self.exchange
        strategy = self.strategy
        try:
            candlestick_data = exchange.getSymbolKlines(\
                symbol, self.kline_interval, strategy.minimum_period)
        except ExchangeConnectionException:
            self.logOrSp('Error getting data from the exchange for exiting order on {}:'.format(symbol), should_print=True)
            self.logOrSp(sys.exc_info(), should_print=True)
            return
        
        if bot.exit_settings.exit_on_signal:
            strategy.setUp(candlestick_data)
            i = len(candlestick_data)-1
            # TODO This only works for LONG bot , but make it work
            # for SHORT bot as well (For SHORT bot, exit signal would
            # be called using checkLongSignal())
            exit_signal = strategy.checkShortSignal(i)

            if exit_signal:
                quantity = self.computeQuantity(order)
                order_type = exchange.ORDER_TYPE_MARKET
                side = exchange.ORDER_SIDE_SELL
                self.placeOrder(
                    symbol,
                    pair,
                    order=order,
                    quantity=quantity,
                    side=side,
                    order_type=order_type)

        else:
            # Calculates quantity of order. 
            # Takes in to account partially filled orders.
            current_price = candlestick_data.iloc[-1]['close']
            stop_loss_value = bot.exit_settings.stop_loss_value 
            profit_target = bot.exit_settings.profit_target

            quantity = self.computeQuantity(order)
            # TODO maybe create setting so that you can indicate which 
            # of the two you want as leading order, atm profit taking 
            # order is set as leading and in updateOpenOrder it is 
            # checked if stop loss was reached and places market order 
            # if that is the case.
            if stop_loss_value is not None and profit_target is not None:
                price = ((Decimal(100) + Decimal(profit_target)) \
                    / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_LIMIT
                side = exchange.ORDER_SIDE_SELL
            elif stop_loss_value is not None:
                price = ((Decimal(100) - Decimal(stop_loss_value)) \
                    / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_STOP_LOSS
                side = exchange.ORDER_SIDE_SELL
            elif profit_target is not None:
                price = ((Decimal(100) + Decimal(profit_target)) \
                    / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_LIMIT
                side = exchange.ORDER_SIDE_SELL

            self.placeOrder(
                symbol=symbol, pair=pair, 
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
        order_params['bot_id'] = self.bot.id
        # print("Order params is")
        # pprint(order_params)
        new_order_model = placeNewOrder(
            self.exchange, symbol, pair, order, self.bot.test_run, order_params)
        
        if new_order_model != None:
            self.syncModels(pair, order, new_order_model)
            self.session.add(new_order_model)
            self.logOrSp('{} Order was placed succesfully on {}'.format(
                    new_order_model.side, symbol), should_print=True)

    def syncModels(self, pair, order, new_order_model):
        """ Sync pairs and orders to new status """
        if order is not None:
            new_order_model.matched_order_id = order.id
            order.is_closed = True
            order.matched_order_id = new_order_model.id
            pair.active = False
            pair.current_order_id = new_order_model.id

        if order is None:
            self.bot.current_balance = self.bot.current_balance \
                - Decimal(self.bot.entry_settings.initial_entry_allocation) \
                    * Decimal(self.bot.starting_balance) / 100
            pair.active = False
            pair.current_order_id = new_order_model.id

    def computeQuantity(self, order):
        """ Compute exit quantity so that also partially 
        filled orders can be handled."""
        if order.side == self.exchange.ORDER_SIDE_BUY:
            exit_quantity = order.executed_quantity
        elif order.side == self.exchange.ORDER_SIDE_SELL:
            exit_quantity = Decimal(order.original_quantity) \
                - Decimal(order.executed_quantity)
        return exit_quantity

    def logOrSp(self, message, should_print=False, force=False):
        if self.sp_on and self.sp != None:
            self.sp.stop()
            if should_print:
              logger.info(message)
            else:
                self.sp.text = message
            self.sp.start()
        elif self.logger_on or force:
            logger.info(message)
