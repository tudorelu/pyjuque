import os 
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)
from pyjuque.Engine import Models # pylint: disable=E0401
from tests.utils import get_session # pylint: disable=E0401
import unittest
from unittest.mock import patch
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as db


class TestSqliteDecimal(unittest.TestCase):
    
    def setUp(self):
        self.scale = 13
        self.sqlite_decimal = Models.SqliteDecimal(self.scale)
        
    def test_initial_value(self):
        """ test initialization for sqlitedecimal class """
        self.assertEqual(self.sqlite_decimal.scale, self.scale)
        self.assertEqual(self.sqlite_decimal.multiplier_int, 10**self.scale)

    # Not used atm 
    def test_process_bind_param(self):
        """ test if values are correctly converted to sqlite values"""
        pass
    
    # Not used atm
    def test_process_result_value(self):
        """test if sqlite values are correctly converted to normal values"""
        pass


class TestOrder(unittest.TestCase):
    
    def test_create_order_table(self):
        """ tests initialization of order table """
        order_table = Models.OrderModel()
        self.assertEqual(order_table.__tablename__, 'order')
        self.assertEqual(order_table.bot_id, None)
        self.assertEqual(order_table.symbol, None)
        self.assertEqual(order_table.timestamp, None)
        self.assertEqual(order_table.entry_price, None)
        self.assertEqual(order_table.take_profit_price, None)
        self.assertEqual(order_table.stop_price, None)
        self.assertEqual(order_table.original_quantity, None)
        self.assertEqual(order_table.executed_quantity, None)
        self.assertEqual(order_table.status, None)
        self.assertEqual(order_table.side, None)
        self.assertEqual(order_table.is_entry, None)
        self.assertEqual(order_table.is_closed, None)
        self.assertEqual(order_table.matched_order_id, None)
        self.assertEqual(order_table.is_test, None)


class TestPair(unittest.TestCase):

    def test_create_pair_table(self):
        """ tests initialization of pair table """
        pair_table = Models.PairModel()
        self.assertEqual(pair_table.__tablename__, 'pair')
        self.assertEqual(pair_table.id, None)
        self.assertEqual(pair_table.bot_id, None)
        self.assertEqual(pair_table.symbol, None)
        self.assertEqual(pair_table.active, None)
        self.assertEqual(pair_table.current_order_id, None)
        self.assertEqual(pair_table.profit_loss, None)


class TestCreateBot(unittest.TestCase):
    """Unittests to test creating and storing a bot"""

    def test_create_bot_table(self):
        """ tests initialization of bot table """
        bot_table = Models.TABotModel()
        self.assertEqual(bot_table.__tablename__, 'ta_bot')
        self.assertEqual(bot_table.id, None)
        self.assertEqual(bot_table.name, None)
        self.assertEqual(bot_table.is_running, None)
        self.assertEqual(bot_table.test_run, None)
        self.assertEqual(bot_table.quote_asset, None)
        self.assertEqual(bot_table.starting_balance, None)
        self.assertEqual(bot_table.current_balance, None)
        self.assertEqual(bot_table.profit_loss, None)

    def test_create_btc_bot(self):
        """ tests storing and querying a bot that trades with btc as quote asset. """
        session = get_session()
        self.assertEqual(len(session.query(Models.TABotModel).all()), 0)
        
        # Create ADABOT
        adabot = Models.TABotModel(
            name="ada_test_bot",
            quote_asset = 'BTC',
            starting_balance = 1,
            current_balance = 1,
            test_run=True
        )

        session.add(adabot)
        session.commit()
        self.assertEqual(len(session.query(Models.TABotModel).all()), 1)

        adabot = session.query(Models.TABotModel).filter_by(name="ada_test_bot").first()
        self.assertEqual(adabot.test_run, True)
        self.assertEqual(adabot.quote_asset, 'BTC')
        self.assertEqual(adabot.starting_balance, 1)
        self.assertEqual(adabot.current_balance, 1)
        self.assertEqual(adabot.profit_loss, 100)  


class TestBot(unittest.TestCase):
    ''' Test the methods within Bot, actually sort of an integration test already.'''    
    
    def setUp(self):
        """Create a bot with 2 pairs and 1 open orders"""

        # define bot params
        self.bot_name = 'ada_test_bot'
        self.bot_id = 1
        self.starting_balance = 2
        self.current_balance = 3
        self.profit_target = 4
        self.test_run = True
        self.quote_asset = 'BTC'
        
        # define pair params
        self.pair_id_ada = 2
        self.symbol_ada = 'ADABTC'
        self.profit_loss_ada = 5

        self.pair_id_eth = 3
        self.symbol_eth = 'ETHBTC'
        self.profit_loss_eth = 6

        # define order params
        self.order_id = 1
        self.order_symbol = self.symbol_eth
        self.entry_price = 2
        self.original_quantity = 3
        self.executed_quantity = 4
        self.status = 'NEW'
        self.side = 'BUY'
        self.is_test = True

        self.session = get_session()
        self.assertEqual(len(self.session.query(Models.TABotModel).all()), 0)

        # Create bot
        bot = Models.TABotModel(
            id=self.bot_id,
            name=self.bot_name,
            quote_asset=self.quote_asset,
            starting_balance=self.starting_balance,
            current_balance=self.current_balance,
            test_run=self.test_run,
        )

        # TODO Should check if pair contains the quote asset saved in bot.
        # Create ETHBTC pair
        ethpair = Models.PairModel(
            id=self.pair_id_eth,
            bot_id=self.bot_id,
            symbol=self.symbol_eth,
            profit_loss=self.profit_loss_eth,
        )
        # Create ADABTC pair
        adapair = Models.PairModel(
            id=self.pair_id_ada,
            bot_id=self.bot_id,
            symbol=self.symbol_ada,
            profit_loss=self.profit_loss_ada,
        )

        # Create ethereum buy order
        ethorder = Models.OrderModel(
            id=self.order_id,
            bot_id=self.bot_id,
            symbol=self.order_symbol,
            entry_price=self.entry_price,
            original_quantity=self.original_quantity,
            executed_quantity=self.executed_quantity,
            status=self.status,
            side=self.side,
            is_test=self.is_test,
        )

        self.session.add(bot)
        self.session.add(adapair)
        self.session.add(ethpair)
        self.session.add(ethorder)
        self.session.commit()

        self.bot = self.session.query(Models.TABotModel).filter_by(name=self.bot_name).first()

    def test_getActivePairs(self):
        """ test getActivePairs method """
        allpairs = self.bot.getActivePairs(self.session)

        for pair in allpairs:
            if pair.symbol == self.symbol_eth:
                eth_btc_pair = pair
            else:
                adabtcpair = pair

        # check if adabtc pair was stored correctly
        self.assertEqual(adabtcpair.id, self.pair_id_ada)
        self.assertEqual(adabtcpair.bot_id, self.bot_id)
        self.assertEqual(adabtcpair.symbol, self.symbol_ada)
        self.assertEqual(adabtcpair.active, True)
        self.assertEqual(adabtcpair.current_order_id, None)
        self.assertEqual(adabtcpair.profit_loss, self.profit_loss_ada)

        # check if ethbtc pair was stored correctly
        self.assertEqual(eth_btc_pair.id, self.pair_id_eth)
        self.assertEqual(eth_btc_pair.bot_id, self.bot_id)
        self.assertEqual(eth_btc_pair.symbol, self.symbol_eth)
        self.assertEqual(eth_btc_pair.active, True)
        self.assertEqual(eth_btc_pair.current_order_id, None)
        self.assertEqual(eth_btc_pair.profit_loss, self.profit_loss_eth)

    def test_getPair(self):
        """ test getPairWithSymbol method """
        eth_btc_pair = self.bot.getPair(self.session, self.symbol_eth)

        # check if ethbtc pair was stored correctly
        self.assertEqual(eth_btc_pair.id, self.pair_id_eth)
        self.assertEqual(eth_btc_pair.bot_id, self.bot_id)
        self.assertEqual(eth_btc_pair.symbol, self.symbol_eth)
        self.assertEqual(eth_btc_pair.active, True)
        self.assertEqual(eth_btc_pair.current_order_id, None)
        self.assertEqual(eth_btc_pair.profit_loss, self.profit_loss_eth)
    
    def test_getOpenOrders(self):
        """ test getOpenOrders() symbol """
        all_orders = self.bot.getOpenOrders(self.session)

        for order in all_orders:
            if order.symbol == self.symbol_eth:
                eth_btc_order = order
        
        self.assertEqual(eth_btc_order.id, str(self.order_id))
        self.assertEqual(eth_btc_order.bot_id,self.bot_id)
        self.assertEqual(eth_btc_order.symbol,self.symbol_eth)
        self.assertEqual(eth_btc_order.entry_price,self.entry_price)
        self.assertEqual(eth_btc_order.take_profit_price,None)
        self.assertEqual(eth_btc_order.stop_price,None)
        self.assertEqual(eth_btc_order.original_quantity,self.original_quantity)
        self.assertEqual(eth_btc_order.executed_quantity,self.executed_quantity)
        self.assertEqual(eth_btc_order.status,self.status)
        self.assertEqual(eth_btc_order.side,self.side)
        self.assertEqual(eth_btc_order.is_entry,True)
        self.assertEqual(eth_btc_order.is_closed,False)
        self.assertEqual(eth_btc_order.matched_order_id,None)
        self.assertEqual(eth_btc_order.is_test,self.is_test)

if __name__ == '__main__':
    unittest.main()