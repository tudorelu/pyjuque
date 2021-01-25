# app/tests/test_order_management.py
import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)

# DB Tools
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alchemy_mock.mocking import AlchemyMagicMock
# Testing Tools
import unittest
from mock import Mock
from tests.utils import timeit, get_session
from unittest.mock import patch
from freezegun import freeze_time
from copy import deepcopy
# Other Tools
import json
import pandas as pd
import datetime as dt
# Pyjuque Modules
from pyjuque.Exchanges.Binance import Binance 
from pyjuque.Strategies.EMAXStrategy import EMAXStrategy 
from pyjuque.Engine import backtest, BotController, OrderModel as Order, PairModel as Pair, \
    TABotModel as Bot, EntrySettingsModel as EntrySettings, ExitSettingsModel as ExitSettings
from pyjuque.Plotting import PlotData 

class OrderManagementTests(unittest.TestCase):
    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):	
        self.exchange = Binance()
        self.df_BTCUSD_1k = pd.read_csv('./tests/data/BTCUSD_1m_1k.csv')
        self.df_BTCUSD_10k = pd.read_csv('./tests/data/BTCUSD_1m_10k.csv')
        self.df_ADABTC_1k = pd.read_csv('./tests/data/ADABTC_1m_1k.csv')
        
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
        self.order_1_id = 1
        self.order_2_id = 2
        self.order_symbol = self.symbol_eth
        self.entry_price = 2
        self.original_quantity = 3
        self.executed_quantity = 4
        self.status = 'NEW'
        self.is_closed = True
        self.side = 'BUY'
        self.is_test = True
        self.session = get_session()
        self.assertEqual(len(self.session.query(Bot).all()), 0)

        # Create bot
        bot = Bot(
            id=self.bot_id,
            name=self.bot_name,
            quote_asset=self.quote_asset,
            starting_balance=self.starting_balance,
            current_balance=self.current_balance,
            # profit_target=self.profit_target,
            test_run=self.test_run,
            )
        # Create entry and exit settings
        entrysets = EntrySettings(
            id = 1,
            name ='TimStoploss',
            initial_entry_allocation = 0.01,
            signal_distance = 0.2,  # in %
            )
        exitsets = ExitSettings(
            id=1,
            name='TimLoss',
            profit_target = 1,      # in %
            stop_loss_value = 10,   # in %
            exit_on_signal=False
            )
        bot.entry_settings = entrysets
        bot.exit_settings = exitsets

        # Create ETHBTC pair
        ethpair = Pair(
            id=self.pair_id_eth,
            bot_id=self.bot_id,
            symbol=self.symbol_eth,
            profit_loss=self.profit_loss_eth,
        )
        # Create ADABTC pair
        adapair = Pair(
            id=self.pair_id_ada,
            bot_id=self.bot_id,
            symbol=self.symbol_ada,
            profit_loss=self.profit_loss_ada,
        )

        # Create ethereum buy order
        eth_order = Order(
            id=self.order_1_id,
            bot_id=self.bot_id,
            symbol=self.order_symbol,
            entry_price=self.entry_price,
            original_quantity=self.original_quantity,
            executed_quantity=self.executed_quantity,
            status=self.status,
            side=self.side,
            is_test=self.is_test,
        )

        eth_order_closed = Order(
            id=self.order_2_id,
            bot_id=self.bot_id,
            symbol=self.order_symbol,
            entry_price=self.entry_price,
            original_quantity=self.original_quantity,
            executed_quantity=self.executed_quantity,
            is_closed=self.is_closed,
            status=self.status,
            side=self.side,
            is_test=self.is_test,
        )
        self.session.add(bot)
        self.session.add(adapair)
        self.session.add(ethpair)
        self.session.add(eth_order)
        self.session.add(eth_order_closed)
        self.session.commit()

        self.bot = self.session.query(Bot).filter_by(name=self.bot_name).first()
        self.strategy = EMAXStrategy(5, 30)

        self.om  = BotController(
            bot=self.bot, 
            session=self.session, 
            exchange=self.exchange, 
            strategy=self.strategy)

    # executed after each test
    def tearDown(self):
        pass

    ###############
    #### tests ####
    ###############

    @patch('pyjuque.Engine.BotController.tryEntryOrder')
    @patch('pyjuque.Engine.BotController.tryExitOrder')
    def test_execute_bot(self, mock_try_exit_order, mock_try_entry_order):
        """ Test execute bot method in OrderManagement"""
        self.om.executeBot()
        self.assertEqual(mock_try_entry_order.call_count, 2)
        self.assertEqual(mock_try_exit_order.call_count, 1)

    @patch('pyjuque.Exchanges.Binance.Binance.getSymbolKlines')
    def test_try_entry_order(self, mock_getSymbolKlines):
        """ Test entry order method in OrderManagement. """

        pair = self.bot.getPairWithSymbol(self.session, self.symbol_eth)
        mock_getSymbolKlines.return_value = self.df_ADABTC_1k

        # Case where false buy signal is returned by strategy.
        with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.setUp') as mockSetupStrategy:
            with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.checkLongSignal', return_value = False):
                with patch('pyjuque.Engine.Models.Order') as mockOrder:
                    self.om.tryEntryOrder(pair)
                    self.assertEqual(mockSetupStrategy.call_count, 1)
                    self.assertEqual(mockOrder.call_count, 0)

        # Create mock sqlAlchemy session
        mock_session = AlchemyMagicMock()

        # create mock orderManagement object with mock db session
        om_mock_database = BotController(
            session=mock_session, 
            bot=self.bot, 
            exchange=self.exchange, 
            strategy=self.strategy
        )

        # Case where true buy signal is returned when test_run.
        with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.setUp') as mockSetupStrategy:
            with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.checkLongSignal', return_value = True):
                om_mock_database.tryEntryOrder(pair)
                self.assertEqual(mockSetupStrategy.call_count, 1)
                self.assertEqual(mock_session.add.call_count, 1)		
                # self.assertEqual(mock_session.commit.call_count, 2)					

        # Create deepcopy of bot object and set test_run to False
        self.bot_not_test = deepcopy(self.bot)
        self.bot_not_test.test_run = False

        # Create mock sqlAlchemy session
        mock_session = AlchemyMagicMock()
        
        # create mock OrderManagement object with mock db session and real run.
        om_mock_database = BotController(
            session=mock_session, 
            bot=self.bot_not_test, 
            exchange=self.exchange, 
            strategy=self.strategy
        )

        # Case where true buy signal is returned when not a test_run.										
        with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.setUp') as mockSetupStrategy:
            with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.checkLongSignal', return_value = True):
                with patch('pyjuque.Exchanges.Binance.Binance.placeLimitOrder', return_value = 'success') as mock_place_limit_order:
                    with patch('pyjuque.Exchanges.Binance.Binance.updateSQLOrderModel') as mock_updateSQLOrder:
                        om_mock_database.tryEntryOrder(pair)
                        self.assertEqual(mock_place_limit_order.call_count, 1)
                        self.assertEqual(mock_updateSQLOrder.call_count, 1)
                        self.assertEqual(mockSetupStrategy.call_count, 1)
                        self.assertEqual(mock_session.add.call_count, 1)		
                        # self.assertEqual(mock_session.commit.call_count, 2)		

        # Create new mock db session
        mock_session = AlchemyMagicMock()
        om_mock_database = BotController(
            session=mock_session, 
            bot=self.bot_not_test, 
            exchange=self.exchange, 
            strategy=self.strategy
        )

        # Case where true buy signal but placeLimitOrder had an error.									
        with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.setUp') as mockSetupStrategy:
            with patch('pyjuque.Strategies.EMAXStrategy.EMAXStrategy.checkLongSignal', return_value = True):
                with patch('pyjuque.Exchanges.Binance.Binance.placeLimitOrder', return_value = 'code') as mock_place_limit_order:
                    with patch('pyjuque.Exchanges.Binance.Binance.updateSQLOrderModel') as mock_updateSQLOrder:
                        om_mock_database.tryEntryOrder(pair)
                        self.assertEqual(mock_place_limit_order.call_count, 1)
                        self.assertEqual(mock_updateSQLOrder.call_count, 0)
                        self.assertEqual(mockSetupStrategy.call_count, 1)
                        # self.assertEqual(mock_session.add.call_count, 1)		
                        # self.assertEqual(mock_session.commit.call_count, 2)
                        # self.assertEqual(mock_session.query.return_value.filter.return_value.delete.call_count, 1)			
    
    def test_try_exit_order(self):
        pass
                
if __name__ == "__main__":
    unittest.main()
