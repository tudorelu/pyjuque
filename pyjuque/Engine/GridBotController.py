import sys
from os import getenv
from yaspin import yaspin
from pprint import pprint
from decimal import Decimal
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from pyjuque.Engine.Models import GridBotModel, getSession
from pyjuque.Engine.OrderManager import *

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GridBotController:

    def __init__(self, name = None):
        self.status_printer = None
        self.screen = False
        if name == None:
            pass
            # print('GridBot is nonexistent, ' 
            #     'please call self.create() '
            #     'with the required parameters')
        else:
            session = getSession('sqlite:///{}.db'.format(name))
            bot_model = session.query(GridBotModel).first()
            if bot_model == None:
                pass
                # print('GridBot is nonexistent, '
                #     'please call self.create() '
                #     'with the required parameters')
            else:
                # print('GridBot found!')
                self.bot_model = bot_model
                self.name = name
                self.session = session
                self.symbol = bot_model.symbol
                self.total_amount = bot_model.starting_balance
                self.trade_amount = bot_model.trade_amount
                self.trade_step = bot_model.trade_step
                self.test_mode = bot_model.test_run
                self.exchange_name = bot_model.exchange.upper()
                self.exchange = CcxtExchange(bot_model.exchange.lower(), {
                    'apiKey': getenv('{}_API_KEY'.format(self.exchange_name)), 
                    'secret': getenv('{}_API_SECRET'.format(self.exchange_name)),
                    'password': getenv('{}_PASSWORD'.format(self.exchange_name)),
                    'timeout': 30000,
                    # 'verbose': True,
                    'enableRateLimit': True,
                })


    def create(self, exchange, symbol, total_amount, trade_amount, trade_step, total_trades, test_mode=False):
        self.exchange = exchange
        self.exchange_name = self.exchange.exchange_id.upper()
        self.symbol = symbol
        self.total_amount = total_amount
        self.trade_amount = trade_amount
        self.trade_step = trade_step
        self.total_trades = total_trades
        self.test_mode = test_mode
        self.name = 'GridBot_{}_{}_{}_{}_{}'.format(
            self.exchange_name, 
            symbol.replace('/', ''), 
            str(int(total_amount)), 
            str(int(trade_amount*total_amount)), 
            str(trade_step*100).replace('.', 'point'))
        if test_mode:
            self.name = self.name+'_test'
            raise NotImplementedError('Test Mode not implemented for GridBot')
        else:
            self.name = self.name+'_live'
        # print('Bot name is {}'.format(self.name))
        self.session = getSession('sqlite:///{}.db'.format(self.name))

        bot_model = self.session.query(GridBotModel).first()
        if bot_model == None:
            self._initializeDatabase()
        else:
            self.bot_model = bot_model


    def _initializeDatabase(self):
        """ Function that initializes the database
        by creating a bot with two pairs. """
        self.bot_model = GridBotModel(
            name = self.name,
            symbol = self.symbol,
            exchange = self.exchange.exchange_id,
            starting_balance = self.total_amount,
            current_balance = self.total_amount,
            trade_amount = self.trade_amount,
            trade_step = self.trade_step,
            test_run = self.test_mode)
        self.session.add(self.bot_model)
        self.session.commit()


    def executeBot(self):
        ticker = self.exchange.ccxt.fetchTicker(self.symbol)
        last_price = Decimal(ticker['last'])
        open_orders = self.bot_model.getOpenOrders(self.session)
        if len(open_orders) == 0:
            # Place Initial Buy Orders
            self.status_printer.text = 'Palcing Initial Orders'
            self.placeInitialOrders(last_price)
            open_orders = self.bot_model.getOpenOrders(self.session)
        for order in open_orders:
            self.status_printer.text = 'Checking Placed Orders'
            self.updateOpenOrder(order, last_price)
        self.updateLastOrder(last_price)
        self.session.commit()


    def placeInitialOrders(self, last_price):
        for i in range(self.total_trades):
            buy_price = last_price - last_price * Decimal(i+1) * Decimal(self.trade_step)
            order = self.placeOrder(
                symbol=self.symbol, side='buy', price=buy_price,  
                quantity=self.trade_amount, order_type='limit', 
                is_entry=True)
            order.position_id = i
        self.session.commit()


    def updateOpenOrder(self, order, last_price):
        if not self.test_mode: 
            # try:
            exchange_order_info = self.exchange.getOrder(order.symbol, order.id, is_custom_id=True)
            # except Exception:
            #     self.log('Error getting data from the exchange for updating open order on {}.'.format(self.symbol))
            #     self.log(sys.exc_info())
            #     return
        else:
            raise NotImplementedError('Test Mode not implemented for GridBot')
        
        # print('Order Info:')
        # pprint(exchange_order_info)
        order.side = exchange_order_info['side']
        order.status = exchange_order_info['status']
        order.executed_quantity = exchange_order_info['filled']
        if exchange_order_info['fee'] != None:
            order.executed_quantity = exchange_order_info['filled'] + exchange_order_info['fee']['cost']
        if (order.side == 'buy'):
            # buy order was filled, place exit order.
            if (order.status == 'closed'):
                self.screen.clear()
                self.screen.refresh()
                # pprint(exchange_order_info)
                self.log('Buy order at {} filled, place exit.'.format(order.price))
                self.placeExitOrder(order)
                self.placeFarthestEntryOrder(last_price)
            elif (order.status in ['canceled', 'expired', 'rejected']):
                if order.executed_quantity > 0:
                    self.log('Buy order at {} canceled, but partially filled, place exit.'.format(order.price))
                    self.placeExitOrder(order)
                    self.placeFarthestEntryOrder(last_price)
                else:
                    order.is_closed = True
        # sell order 
        if (order.side == 'sell'):
            # sell order was filled
            if (order.status == 'closed'):
                self.screen.clear()
                self.screen.refresh()
                # pprint(exchange_order_info)
                self.log('Sell order at {} filled, cancel farthest buy order and replace with new buy order.'.format(order.price))
                self.cancelFarthestEntryOrder(last_price)
                self.placeEntryOrder(order)
                order.is_closed = True
            # sell order was rejected by engine of exchange
            # if (order.status in ['rejected', 'expired', 'canceled']):
            #     original_buy_order = self.reviveOriginalBuyOrder(order)
            #     self.placeExitOrder(original_buy_order)


    def placeEntryOrder(self, exit_order):
        # entry_order = self.session.query(Order).filter_by(matched_order_id=exit_order.id)
        buy_price = exit_order.price * Decimal(1 - self.trade_step)
        self.placeOrder(
            symbol = self.symbol,
            price = buy_price, 
            quantity = exit_order.executed_quantity, 
            side = 'buy', 
            order_type = 'limit', 
            is_entry=True)


    def placeExitOrder(self, entry_order):
        sell_price = entry_order.price * Decimal(1 + 2 * self.trade_step)
        self.placeOrder(
            symbol = self.symbol,
            entry_order = entry_order, 
            price = sell_price, 
            quantity = entry_order.executed_quantity, 
            side = 'sell', 
            order_type = 'limit')


    def updateLastOrder(self, last_price):
        open_orders = [order for order in self.bot_model.getOpenOrders(self.session) if order.side == 'buy']
        if len(open_orders) == 0:
            return
        farthest_order = None
        closest_order = None
        max_difference = 0
        min_difference = 10000
        for order in open_orders:
            difference = last_price - order.price
            if difference > max_difference:
                max_difference = difference
                farthest_order = order
            if difference < min_difference:
                min_difference = difference
                closest_order = order
        if min_difference > last_price * Decimal(2 * self.trade_step):
            order_result = self.exchange.cancelOrder(
                farthest_order.symbol, farthest_order.id, is_custom_id=True)
            farthest_order.status = 'canceled'
            farthest_order.is_closed = True
            buy_price = closest_order.price * Decimal(1 + self.trade_step)
            self.placeOrder(
                symbol = self.symbol,
                price = buy_price, 
                quantity = farthest_order.original_quantity, 
                side = 'buy', 
                order_type = 'limit',
                is_entry=True)


    def cancelFarthestEntryOrder(self, last_price):
        open_orders = [order for order in self.bot_model.getOpenOrders(self.session) if order.side == 'buy']
        if len(open_orders) == 0:
            return
        farthest_order = None
        max_difference = 0
        for order in open_orders:
            difference = last_price - order.price
            if difference > max_difference:
                max_difference = difference
                farthest_order = order
        order_result = self.exchange.cancelOrder(farthest_order.symbol, farthest_order.id, is_custom_id=True)
        farthest_order.status = 'canceled'
        farthest_order.is_closed = True


    def placeFarthestEntryOrder(self, last_price):
        open_orders = [order for order in self.bot_model.getOpenOrders(self.session) if order.side == 'buy']
        if len(open_orders) == 0:
            buy_price = last_price * Decimal(1 - self.trade_step)
            self.placeOrder(
                symbol = self.symbol,
                price = buy_price, 
                quantity = self.trade_amount, 
                side = 'buy', 
                order_type = 'limit',
                is_entry=True)
            return
        farthest_order = None
        max_difference = 0
        for order in open_orders:
            difference = last_price - order.price
            if difference > max_difference:
                max_difference = difference
                farthest_order = order
        buy_price = farthest_order.price * Decimal(1 - self.trade_step)
        self.placeOrder(
            symbol = self.symbol,
            price = buy_price, 
            quantity = self.trade_amount, 
            side = 'buy', 
            order_type = 'limit',
            is_entry=True)


    def placeOrder(self, entry_order=None, **order_params):
        """ Create Order model and place order to exchange. """
        order_params['bot_id'] = self.bot_model.id
        new_order = placeNewOrder(
            exchange = self.exchange, 
            symbol = self.symbol, 
            order = entry_order, 
            test_mode = self.test_mode,
            order_params = order_params)
        if new_order != None:
            self.syncModels(entry_order, new_order)
            self.session.add(new_order)
        return new_order


    def syncModels(self, entry_order, new_order):
        """ Sync orders to new status """
        if entry_order is not None:
            new_order.matched_order_id = entry_order.id
            entry_order.is_closed = True
            entry_order.matched_order_id = new_order.id
        else:
            self.bot_model.current_balance = self.bot_model.current_balance \
                - Decimal(self.trade_amount) * Decimal(self.bot_model.starting_balance)


    def log(self, message, should_print=True):
        # if self.screen:
        #     self.screen.clear()
        #     self.screen.refresh()
        if self.status_printer != None:
            self.status_printer.stop()
            if should_print:
                logger.info(message)
            else:
                self.status_printer.text = message
            self.status_printer.start()
        elif should_print:
            logger.info(message)
