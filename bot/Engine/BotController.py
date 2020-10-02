import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from traceback import print_exc
from decimal import Decimal
from uuid import uuid4
import time
import math
from bot.Exchanges.Binance import Binance # pylint: disable=E0401
from bot.Engine.Models import Bot, Pair, Order # pylint: disable=E0401

class BotController:

    def __init__(self, session, bot, exchange, strategy):
        self.bot = bot
        self.session = session
        self.exchange = exchange
        self.strategy = strategy
        self.test_mode = bot.test_run
        self.kline_interval = '5m'	
    
    def executeBot(self):
            """ The main execution loop of the bot """

            # Step 1: Retreive all pairs for a particular bot
            logger.info("Getting active pairs:")
            active_pairs = self.bot.getActivePairs(self.session)
            logger.info("Number of active_pairs: {}".format(len(active_pairs)))

            # Step 2 For Each Pair:
            #		Retreive current market data 
            # 	Compute Indicators & Check if Strategy is Fulfilled
            #		IF Fulfilled, palce order (Save order in DB)
            logger.info("Checking signals on pairs...")
            for pair in active_pairs:
                    self.tryEntryOrder(pair)

            # Step 3: Retreive all open orders on the bot
            logger.info("Getting open orders:")
            open_orders = self.bot.getOpenOrders(self.session)
            logger.info("Number of open orders: {}".format(len(open_orders)))

            # Step 4: For Each order that was already placed by the bot 
            # and was not filled before, check status:
            #		IF Filled -> If entry order, place exit order
            #							-> If exit order, success (take profit), or 
            # 															failure (stop loss): Resume trading!
            logger.info("Checking orders state...")
            for order in open_orders:
                    self.updateOpenOrder(order)


    def tryEntryOrder(self, pair):
        """
        Gets the latest market data and runs the strategy off of it. If strategy returns entry signal, entry is made.
        """
        bot = self.bot
        exchange = self.exchange
        strategy = self.strategy

        symbol = pair.symbol
        logger.info("Checking signal on {}".format(symbol))

        df = exchange.getSymbolKlines(symbol, self.kline_interval, limit=strategy.minimum_period)
        entry_signal = strategy.shouldEntryOrder(df)
        
        if entry_signal:
            side = 'BUY'
            quote_qty = Decimal(bot.starting_balance) * Decimal(bot.entry_settings.initial_entry_allocation) / 100
            if bot.entry_settings.signal_distance == 0:
                desired_price = Decimal(df.iloc[-1]['close'])
                quantity = quote_qty / desired_price
                self.placeNewOrder(symbol=symbol, pair=pair, quantity=quantity, side=side, order_type=exchange.ORDER_TYPE_MARKET, is_entry=True)
            else:
                desired_price = Decimal(df.iloc[-1]['close']) * Decimal((100 - bot.entry_settings.signal_distance) / 100 )
                quantity = quote_qty / desired_price
                price = desired_price
                self.placeNewOrder(symbol=symbol, pair=pair, price=price, quantity=quantity, side=side, order_type=exchange.ORDER_TYPE_LIMIT, is_entry=True)              

            self.session.commit()

    def updateOpenOrder(self, order):
        """
        Checks the status of an open order and updates it
        """
        exchange = self.exchange

        # get pair from database
        pair:Pair = self.bot.getPairWithSymbol(self.session, order.symbol)
        # get info of order from exchange
        if not self.test_mode:
            exchange_order_info = exchange.getOrderInfo(order.symbol, order.id)
        else:
            exchange_order_info = self.simulateOrderInfo(order)
        # check for valid response from exchange
        if not exchange.isValidResponse(exchange_order_info):
            logger.warning('Exchange order info could not be retrieved!, message from exchange: {}'.format(exchange_order_info))
            return
        # update order params.
        order.side = exchange_order_info['side']
        order.status = exchange_order_info['status']
        order.executed_quantity = exchange_order_info['executedQty']

        # Order has been canceled by the user
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_CANCELED):
            if order.executed_quantity > 0:
                self.tryExitOrder(order, pair)
            else:
                self.processClosedPosition(order, pair)

        # buy order was filled, place exit order.
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_FILLED):
            self.tryExitOrder(order, pair)

        # buy order has been accepted by engine
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_NEW):
            self.updateOpenBuyOrder(order, pair)

        # buy order that has been partially filled
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
            self.updateOpenBuyOrder(order, pair)

        # buy order was rejected, not processed by engine
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_REJECTED):
            self.processClosedPosition(order, pair)

        # buy order expired, i.e. FOK orders with no fill or due to maintenance by exchange.
        if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_EXPIRED):
            if order.executed_quantity > 0:
                self.tryExitOrder(order, pair)
            else:
                self.processClosedPosition(order, pair)

        # sell order was cancelled by user.
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_CANCELED):
            # query buy order to again place a sell order for that buy order.
            original_buy_order = self.reviveOriginalBuyOrder(order)
            self.tryExitOrder(original_buy_order, pair)

        # sell order was filled
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_FILLED):
            self.processClosedPosition(order, pair)

        # sell order was accepted by engine of exchange
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_NEW):
            self.updateOpenSellOrder(order, pair)

        # sell order was partially filled
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
            self.updateOpenSellOrder(order, pair)

        # sell order was rejected by engine of exchange
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_REJECTED):
            original_buy_order = self.reviveOriginalBuyOrder(order)
            self.tryExitOrder(original_buy_order, pair)

        # sell order expired, i.e. due to FOK orders or partially filled market orders
        if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_EXPIRED):
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
        Looks to close an open buy order based on strategy specified in entry settings.
        For now you can only close orders based on time passed.
        """
        exchange = self.exchange

        # How can we guarantee timestamp of exchange is always in ms?
        if (order.timestamp).timestamp() - time.time()*1000 > self.bot.entry_settings.open_buy_order_time_out:
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
        For now only supports placing stop loss market order when position goes against us ( basically simple oco order variant ).
        """
        exchange = self.exchange
        bot = self.bot
        strategy = self.strategy
        
        candlestick_data = exchange.getSymbolKlines(order.symbol, self.kline_interval, strategy.minimum_period)
        current_price = candlestick_data.iloc[-1]['close']
        stop_loss_active = bot.exit_settings.stop_loss_value is not None

        if stop_loss_active:
            if ((Decimal(100) - Decimal(bot.exit_settings.stop_loss_value))/Decimal(100)) * Decimal(order.entry_price) >= Decimal(current_price):
                quantity = self.computeQuantity(order)
                side = 'SELL'
                order_type = exchange.ORDER_TYPE_MARKET

                if not self.test_mode:
                    order_result = exchange.cancelOrder(order.symbol, order.id)
                else:
                    order_result = dict(status=self.exchange.ORDER_STATUS_CANCELED, executedQty=0)

                if exchange.isValidResponse(order_result):
                    # TODO probably taking over info from exchange like this will not be modular enough for other exchanges.
                    order.status = order_result['status']
                    order.executed_quantity = order_result['executedQty']

                    self.placeNewOrder( 
                                        symbol=order.symbol, 
                                        pair=pair,
                                        order=order,
                                        quantity=quantity,
                                        order_type=order_type,
                                        side=side
                                        ) 
	
    def tryExitOrder(self, order, pair):
        """ If strategy returns exit signal look to place exit order. """
        bot = self.bot
        symbol = order.symbol
        exchange = self.exchange
        strategy = self.strategy

        candlestick_data = exchange.getSymbolKlines(symbol, self.kline_interval, strategy.minimum_period)
        if bot.exit_settings.exit_on_signal:
            exit_signal = strategy.shouldExitOrder(candlestick_data)

            if exit_signal:
                quantity = self.computeQuantity(order)
                order_type = exchange.ORDER_TYPE_MARKET
                side = 'SELL'
                self.placeNewOrder(
                                symbol, 
                                pair,
                                order=order, 
                                quantity=quantity, 
                                side=side, 
                                order_type=order_type
                                )

        if not bot.exit_settings.exit_on_signal:
            # Calculates quantity of order. Takes in to account partially filled orders.
            current_price = candlestick_data.iloc[-1]['close']
            stop_loss_active = bot.exit_settings.stop_loss_value is not None
            profit_taking_active = bot.exit_settings.profit_target is not None

            quantity = self.computeQuantity(order)
            # TODO maybe create setting so that you can indicate which of the two you want as leading order
            # atm profit taking order is set as leading and in updateOpenOrder it is checked if stop loss was reached
            # and places market order if that is the case.
            if stop_loss_active and profit_taking_active:
                price = ((Decimal(100) + Decimal(bot.exit_settings.profit_target)) / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_LIMIT
                side = 'SELL'
            elif stop_loss_active:
                price = ((Decimal(100) - Decimal(bot.exit_settings.stop_loss_value)) / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_STOP_LOSS
                side = 'SELL'
            elif profit_taking_active:
                price = ((Decimal(100) + Decimal(bot.exit_settings.profit_target)) / Decimal(100)) * Decimal(current_price)
                order_type = exchange.ORDER_TYPE_LIMIT
                side = 'SELL'

            self.placeNewOrder(
                                symbol, 
                                pair,
                                order = order, 
                                price=price, 
                                quantity=quantity, 
                                side=side, 
                                order_type=order_type
                                )


    def processClosedPosition(self, order, pair):
        """ Update status of closed position """
        order.is_closed = True
        pair.active = True
        pair.current_order_id = None

    def placeNewOrder(self, symbol, pair, order = None, **order_params):
        """ Create Order model and place order to exchange. """
        new_order_model = self.createOrderModel(symbol, order_params, order)

        if not self.test_mode:
            new_order_response = self.placeOrderFromOrderModel(new_order_model)
        else:
            new_order_response = dict(message='success')

        if self.exchange.isValidResponse(new_order_response):
            self.exchange.updateSQLOrderModel(new_order_model, new_order_response, self.bot)
            self.syncModels(pair, order, new_order_model)
            self.session.add(new_order_model)
            logger.info('{} Order was placed succesfully'.format(new_order_model.side))

    def createOrderModel(self, symbol, order_params, order):
        """ Create Order Model and fill only mandatory params. Other params are filled after order is filled. """
        if 'price' not in order_params:
            order_params['price'] = None
        if 'take_profit_price' not in order_params:
            order_params['take_profit_price'] = None
        if 'stop_price' not in order_params:
            order_params['stop_price'] = None
        if 'is_entry' not in order_params:
            order_params['is_entry'] = False
        if order is None:
            position_id = str(uuid4())
            entry_price = None
        elif order is not None:
            position_id = order.position_id
            entry_price = order.entry_price      
        
        new_order_model = Order(
                                id = str(uuid4()),
                                position_id = position_id,
                                bot_id = self.bot.id,
                                symbol = symbol,
                                price = order_params['price'],
                                take_profit_price = order_params['take_profit_price'],
                                order_type = order_params['order_type'],
                                stop_price = order_params['stop_price'],
                                original_quantity = order_params['quantity'],
                                side = order_params['side'],
                                is_entry =  order_params['is_entry'],
                                is_test = self.test_mode,
                                entry_price = entry_price,
                                last_checked_time = int(round(time.time() * 1000))
                                )
        return new_order_model

    def placeOrderFromOrderModel(self, order_model):
        """ Places orders from db model to exchange."""
        exchange = self.exchange
        if order_model.order_type == exchange.ORDER_TYPE_LIMIT:
            order_response = exchange.placeLimitOrder(order_model.symbol, order_model.price, order_model.side, order_model.original_quantity, order_model.is_test, custom_id=order_model.id)
        if order_model.order_type == exchange.ORDER_TYPE_MARKET:
            order_response = exchange.placeMarketOrder(order_model.symbol, order_model.side, order_model.original_quantity, order_model.is_test, custom_id=order_model.id)
        if order_model.order_type == exchange.ORDER_TYPE_STOP_LOSS:
            order_response = exchange.placeStopLossMarketOrder(order_model.symbol, order_model.price, order_model.side, order_model.original_quantity, order_model.is_test, custom_id=order_model.id)
        return order_response

    def syncModels(self, pair, order, new_order_model):
        """ Sync pairs and orders to new status """
        if order is not None:        
            new_order_model.matched_order_id = order.id
            order.is_closed = True
            order.matched_order_id = new_order_model.id
            pair.active = False
            pair.current_order_id = new_order_model.id

        if order is None:
            self.bot.current_balance = self.bot.current_balance - Decimal(self.bot.starting_balance) * Decimal(self.bot.entry_settings.initial_entry_allocation) / 100
            pair.active = False
            pair.current_order_id = new_order_model.id    

    def computeQuantity(self, order):
        """ compute exit quantity so that also partially filled orders can be handled."""
        if order.side == 'BUY':
            exit_quantity = order.executed_quantity
        elif order.side == 'SELL':
            exit_quantity = Decimal(order.original_quantity) - Decimal(order.executed_quantity)
        return exit_quantity
    
    def simulateOrderInfo(self, order):
        """ Used when BotController is in test mode. Simulates order info returned by exchange."""
        order_status = dict()
        new_last_checked_time = int(round(time.time() * 1000)) # time in ms
        time_diff = new_last_checked_time - order.last_checked_time
        interval_in_ms = self.klineIntervalToMs(self.kline_interval)
        if  time_diff < interval_in_ms:
            candlestick_data = self.exchange.getSymbolKlines(order.symbol, self.kline_interval, 1)
        else:
            minimum_period = int(math.ceil(time_diff / interval_in_ms))
            candlestick_data = self.exchange.getSymbolKlines(order.symbol, self.kline_interval, minimum_period, start_time=order.last_checked_time)
        
        for _, candle in candlestick_data.iterrows():
            lowest_price = candle['low']
            if order.order_type == self.exchange.ORDER_TYPE_LIMIT:
                if lowest_price <= order.price:
                    order_status['status'] = self.exchange.ORDER_STATUS_FILLED
                    order_status['side'] = order.side
                    order_status['executedQty'] = order.original_quantity
                    break
            elif order.order_type == self.exchange.ORDER_TYPE_MARKET:
                order.price = (candle['open']+candle['close'])/2 # not sure what to set this value to. For now average of open and close of candle.
                order_status['status'] = self.exchange.ORDER_STATUS_FILLED
                order_status['side'] = order.side
                order_status['executedQty'] = order.original_quantity
                break
            elif order.order_type == self.exchange.ORDER_TYPE_STOP_LOSS:
                if lowest_price >= order.price:
                    order_status['status'] = self.exchange.ORDER_STATUS_FILLED
                    order_status['side'] = order.side
                    order_status['executedQty'] = order.original_quantity
                    break
        if not order_status:
            order_status['status'] = self.exchange.ORDER_STATUS_NEW
            order_status['side'] = order.side      
            order_status['executedQty'] = 0

        order.last_checked_time = new_last_checked_time
        return order_status
    
    def klineIntervalToMs(self, kline_interval:str):
        number = int(kline_interval[:-1])
        unit = kline_interval[-1]
        if unit == 'm':
            multiply_by = 1000 * 60
        if unit =='h':
            multiply_by = 1000 * 60 * 60
        if unit == 'd':
            multiply_by = 1000 * 60 * 60 * 24
        if unit == 'w':
            multiply_by = 1000 * 60 * 60 * 24 * 7
        if unit == 'M':
            multiply_by = 1000 * 60 * 60 * 24 * 31 # bit too long does not matter.
        return number * multiply_by