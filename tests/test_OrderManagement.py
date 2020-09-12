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
from utils import timeit
from helper_functions import get_session
from unittest.mock import patch
from freezegun import freeze_time
from copy import deepcopy

# Other Tools
import json
import pandas as pd
import datetime as dt

# Pyjuque Modules
from bot.Exchanges.Binance import Binance # pylint: disable=E0401
from bot.Strategies.EMAXStrategy import EMACrossover # pylint: disable=E0401
from bot.Engine import backtest, OrderManagement, Order, Pair, Bot, Base # pylint: disable=E0401
from bot.Plotter import PlotData # pylint: disable=E0401

class OrderManagementTests(unittest.TestCase):
	############################
	#### setup and teardown ####
	############################

	# executed prior to each test
	def setUp(self):	

		self.exchange = Binance()
		self.df_BTCUSD_1k = pd.read_csv(r'pyjuque/tests/data/BTCUSD_1m_1k.csv')
		self.df_BTCUSD_10k = pd.read_csv(r'pyjuque/tests/data/BTCUSD_1m_10k.csv')
		self.df_ADABTC_1k = pd.read_csv(r'pyjuque/tests/data/ADABTC_1m_1k.csv')
		
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
		self.order_type = self.exchange.ORDER_TYPE_LIMIT

		self.session = get_session()
		self.assertEqual(len(self.session.query(Bot).all()), 0)

		# Create bot
		bot = Bot(
					id=self.bot_id,
					name=self.bot_name,
					quote_asset=self.quote_asset,
					starting_balance=self.starting_balance,
					current_balance=self.current_balance,
					profit_target=self.profit_target,
					test_run=self.test_run,
					)

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
			order_type=self.order_type,
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
			order_type=self.order_type,
		)
		self.session.add(bot)
		self.session.add(adapair)
		self.session.add(ethpair)
		self.session.add(eth_order)
		self.session.add(eth_order_closed)
		self.session.commit()

		
		self.bot = self.session.query(Bot).filter_by(name=self.bot_name).first()
		self.eth_order = self.bot.getOpenOrders(self.session)[0]
		self.eth_pair = self.bot.getPairWithSymbol(self.session, self.order_symbol)
		self.strategy = EMACrossover(5, 30)

		self.om  = OrderManagement(
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

	@patch('bot.Engine.OrderManagement.try_entry_order')
	@patch('bot.Engine.OrderManagement.update_open_order')
	def test_execute_bot(self, mock_update_open_order, mock_try_entry_order):
		""" Test execute bot method in OrderManagement"""
		
		self.om.execute_bot()

		self.assertEqual(mock_try_entry_order.call_count, 2)
		self.assertEqual(mock_update_open_order.call_count, 1)

	@patch('bot.Exchanges.Binance.Binance.getSymbolKlines')
	def test_try_entry_order(self, mock_getSymbolKlines):
		""" Test entry order method in OrderManagement. """

		pair = self.bot.getPairWithSymbol(self.session, self.symbol_eth)
		mock_getSymbolKlines.return_value = self.df_ADABTC_1k

		# Case where false buy signal is returned by strategy.
		with patch('bot.Strategies.EMAXStrategy.EMACrossover.setup') as mockSetupStrategy:
			with patch('bot.Strategies.EMAXStrategy.EMACrossover.checkBuySignal', return_value = False):
				with patch('bot.Engine.Models.Order') as mockOrder:
					self.om.try_entry_order(pair)
					self.assertEqual(mockSetupStrategy.call_count, 1)
					self.assertEqual(mockOrder.call_count, 0)

		# Create mock sqlAlchemy session
		mock_session = AlchemyMagicMock()

		# create mock orderManagement object with mock db session
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot, 
										exchange=self.exchange, 
										strategy=self.strategy
										)

		# Case where true buy signal is returned when test_run.
		with patch('bot.Strategies.EMAXStrategy.EMACrossover.setup') as mockSetupStrategy:
			with patch('bot.Strategies.EMAXStrategy.EMACrossover.checkBuySignal', return_value = True):
				om_mock_database.try_entry_order(pair)
				self.assertEqual(mockSetupStrategy.call_count, 1)
				self.assertEqual(mock_session.add.call_count, 1)		
				self.assertEqual(mock_session.commit.call_count, 2)					

		# Create deepcopy of bot object and set test_run to False
		self.bot_not_test = deepcopy(self.bot)
		self.bot_not_test.test_run = False

		# Create mock sqlAlchemy session
		mock_session = AlchemyMagicMock()

		# create mock OrderManagement object with mock db session and real run.
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot_not_test, 
										exchange=self.exchange, 
										strategy=self.strategy
										)

		# Case where true buy signal is returned when not a test_run.										
		with patch('bot.Strategies.EMAXStrategy.EMACrossover.setup') as mockSetupStrategy:
			with patch('bot.Strategies.EMAXStrategy.EMACrossover.checkBuySignal', return_value = True):
				with patch('bot.Exchanges.Binance.Binance.placeLimitOrder', return_value = 'success') as mock_place_limit_order:
					with patch('bot.Exchanges.Binance.Binance.updateSQLOrderModel') as mock_updateSQLOrder:
						om_mock_database.try_entry_order(pair)
						self.assertEqual(mock_place_limit_order.call_count, 1)
						self.assertEqual(mock_updateSQLOrder.call_count, 1)
						self.assertEqual(mockSetupStrategy.call_count, 1)
						self.assertEqual(mock_session.add.call_count, 1)		
						self.assertEqual(mock_session.commit.call_count, 2)		

		# Create new mock db session
		mock_session = AlchemyMagicMock()
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot_not_test, 
										exchange=self.exchange, 
										strategy=self.strategy
										)

		# Case where true buy signal but placeLimitOrder had an error.									
		with patch('bot.Strategies.EMAXStrategy.EMACrossover.setup') as mockSetupStrategy:
			with patch('bot.Strategies.EMAXStrategy.EMACrossover.checkBuySignal', return_value = True):
				with patch('bot.Exchanges.Binance.Binance.placeLimitOrder', return_value = 'code') as mock_place_limit_order:
					with patch('bot.Exchanges.Binance.Binance.updateSQLOrderModel') as mock_updateSQLOrder:
						om_mock_database.try_entry_order(pair)
						self.assertEqual(mock_place_limit_order.call_count, 1)
						self.assertEqual(mock_updateSQLOrder.call_count, 0)
						self.assertEqual(mockSetupStrategy.call_count, 1)
						self.assertEqual(mock_session.add.call_count, 1)		
						self.assertEqual(mock_session.commit.call_count, 2)
						self.assertEqual(mock_session.query.return_value.filter.return_value.delete.call_count, 1)			
	
	def run_test_update_open_order(self, mock_getOrderInfo, mock_method_path):
		# Create mock sqlAlchemy session
		mock_session = AlchemyMagicMock()
		
		# create mock orderManagement object with mock db session
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot, 
										exchange=self.exchange, 
										strategy=self.strategy
										)
		#Case 
		

		if mock_getOrderInfo.return_value == 'code':
			om_mock_database.update_open_order(self.eth_order)
			self.assertEqual(mock_session.commit.call_count, 0)	
		else:
			with patch(mock_method_path) as mock_method:
				om_mock_database.update_open_order(self.eth_order)
				self.assertEqual(mock_method.call_count, 1)
				self.assertEqual(mock_session.commit.call_count, 1)
	
	@patch('bot.Exchanges.Binance.Binance.getOrderInfo')
	def test_update_open_order(self, mock_getOrderInfo):
		exchange_order_info = dict(side='', status='', executedQty=0)
		
		# No valid response from exchange for order info
		mock_getOrderInfo.return_value = 'code'
		self.run_test_update_open_order(mock_getOrderInfo, None)

		# Canceled Buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_CANCELED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_canceled_buy_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Filled buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_FILLED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.try_exit_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# New Buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_NEW
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.update_open_buy_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Partially filled Buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_PARTIALLY_FILLED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.update_open_buy_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Rejected Buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_REJECTED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_rejected_buy_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Expired Buy order
		exchange_order_info['side'] = 'BUY'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_EXPIRED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_expired_buy_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)
		
		# Canceled Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_CANCELED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_canceled_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Filled Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_FILLED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_filled_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# New Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_NEW
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.update_open_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Partially filled Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_PARTIALLY_FILLED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.update_partially_filled_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Rejected Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_REJECTED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_rejected_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

		# Expired Sell order
		exchange_order_info['side'] = 'SELL'
		exchange_order_info['status'] = self.exchange.ORDER_STATUS_EXPIRED
		mock_getOrderInfo.return_value = exchange_order_info
		mock_method_path = 'bot.Engine.OrderManagement.process_expired_sell_order'
		self.run_test_update_open_order(mock_getOrderInfo, mock_method_path)

	def test_process_canceled_buy_order(self):
		order = deepcopy(self.eth_order)
		order.status = self.exchange.ORDER_STATUS_CANCELED
		order.executed_quantity = 0
		pair = deepcopy(self.eth_pair)
		self.om.process_canceled_buy_order(order, pair)
		self.assertEqual(order.is_closed, True)
		self.assertEqual(pair.active, True)
		self.assertEqual(pair.current_order_id, None)

		order = deepcopy(self.eth_order)
		order.executed_quantity = 2
		with patch('bot.Engine.OrderManagement.try_exit_order') as mock_try_exit_order:
			self.om.process_canceled_buy_order(order, pair)
			self.assertEqual(mock_try_exit_order.call_count, 1)
			self.assertEqual(order.is_closed, False)

	@patch('bot.Strategies.EMAXStrategy.EMACrossover.setup')
	@patch('bot.Strategies.EMAXStrategy.EMACrossover.update_open_buy_order')
	@patch('bot.Exchanges.Binance.Binance.getSymbolKlines')
	@patch('bot.Exchanges.Binance.Binance.cancelOrder')
	def test_update_open_buy_order(self, mock_cancel_order, mock_getSymbolKlines, mock_strategy_update_open_buy_order, mock_setup_strat):
		mock_getSymbolKlines.return_value = pd.DataFrame()
		mock_strategy_update_open_buy_order.return_value = False
		self.om.update_open_buy_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_getSymbolKlines.call_count, 1)
		self.assertEqual(mock_setup_strat.call_count, 1)
		self.assertEqual(mock_strategy_update_open_buy_order.call_count, 1)
		self.assertEqual(mock_cancel_order.call_count, 0)

		mock_strategy_update_open_buy_order.return_value = True
		mock_cancel_order.return_value = dict(executedQty=1, status=self.exchange.ORDER_STATUS_CANCELED)
		with patch('bot.Engine.OrderManagement.process_canceled_buy_order') as mock_process_canceled_buy_order:
			self.om.update_open_buy_order(self.eth_order, self.eth_pair)
			self.assertEqual(mock_cancel_order.call_count, 1)
			self.assertEqual(self.eth_order.executed_quantity, 1)
			self.assertEqual(mock_process_canceled_buy_order.call_count, 1)

	def test_process_rejected_buy_order(self):
		self.om.process_rejected_buy_order(self.eth_order, self.eth_pair)
		self.assertEqual(self.eth_pair.active, True)
		self.assertEqual(self.eth_pair.current_order_id, None)
		self.assertEqual(self.eth_order.is_closed, True)

	def test_process_expired_buy_order(self):
		with patch('bot.Engine.OrderManagement.process_canceled_buy_order') as mock_process_canceled_buy_order:
			self.om.process_expired_buy_order(self.eth_order, self.eth_pair)
			self.assertEqual(mock_process_canceled_buy_order.call_count, 1)
		self.eth_order.executed_quantity = 0
		self.om.process_expired_buy_order(self.eth_order, self.eth_pair)
		self.assertEqual(self.eth_pair.active, True)
		self.assertEqual(self.eth_pair.current_order_id, None)
		self.assertEqual(self.eth_order.is_closed, True)

	@patch('bot.Engine.OrderManagement.try_exit_order')
	def test_process_cancelled_sell_order(self, mock_try_exit_order):
		self.om.process_canceled_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_try_exit_order.call_count, 1)
	
	@patch('bot.Strategies.EMAXStrategy.EMACrossover.setup')
	@patch('bot.Strategies.EMAXStrategy.EMACrossover.update_open_sell_order')
	@patch('bot.Exchanges.Binance.Binance.getSymbolKlines')
	@patch('bot.Exchanges.Binance.Binance.cancelOrder')
	def test_update_open_sell_order(self, mock_cancel_order, mock_getSymbolKlines, mock_strategy_update_open_sell_order, mock_setup_strat):
		mock_getSymbolKlines.return_value = pd.DataFrame()
		mock_strategy_update_open_sell_order.return_value = False, dict()
		self.om.update_open_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_getSymbolKlines.call_count, 1)
		self.assertEqual(mock_setup_strat.call_count, 1)
		self.assertEqual(mock_strategy_update_open_sell_order.call_count, 1)
		self.assertEqual(mock_cancel_order.call_count, 0)

		mock_strategy_update_open_sell_order.return_value = True, dict()
		mock_cancel_order.return_value = dict(executedQty=1, status=self.exchange.ORDER_STATUS_CANCELED)
		with patch('bot.Engine.OrderManagement.place_sell_order') as mock_place_sell_order:
			self.om.update_open_sell_order(self.eth_order, self.eth_pair)
			self.assertEqual(mock_cancel_order.call_count, 1)
			self.assertEqual(self.eth_order.executed_quantity, 1)
			self.assertEqual(mock_place_sell_order.call_count, 1)

	@patch('bot.Engine.OrderManagement.create_order')
	@patch('bot.Engine.OrderManagement.compute_quantity')
	def test_update_partially_filled_sell_order(self, mock_compute_quantity, mock_create_order):
		# Create mock sqlAlchemy session
		mock_session = AlchemyMagicMock()
		
		# create mock orderManagement object with mock db session
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot, 
										exchange=self.exchange, 
										strategy=self.strategy
										)
		self.eth_order.side = 'SELL'
		
		new_order = deepcopy(self.eth_order)
		new_order.id = 1111
		new_order.original_quantity = self.eth_order.original_quantity - self.eth_order.executed_quantity
		mock_create_order.return_value = new_order

		om_mock_database.update_partially_filled_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(self.eth_order.is_closed, True)
		self.assertEqual(self.eth_order.matched_order_id, 1111)
		self.assertEqual(self.eth_pair.active, False)
		self.assertEqual(self.eth_pair.current_order_id, 1111)	

		self.assertEqual(mock_compute_quantity.call_count, 1)
		self.assertEqual(mock_create_order.call_count, 1)
		self.assertEqual(mock_session.add.call_count, 1)

	@patch('bot.Engine.OrderManagement.try_exit_order')
	def test_process_rejected_sell_order(self, mock_try_exit_order):
		self.om.process_rejected_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_try_exit_order.call_count, 1)

	@patch('bot.Engine.OrderManagement.try_exit_order')
	def test_process_expired_sell_order(self, mock_try_exit_order):
		self.om.process_expired_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_try_exit_order.call_count, 1)

	def test_process_filled_sell_order(self):
		self.om.process_filled_sell_order(self.eth_order, self.eth_pair)
		self.assertEqual(self.eth_order.is_closed, True)
		self.assertEqual(self.eth_pair.active, True)
		self.assertEqual(self.eth_pair.current_order_id, None)

	@patch('bot.Strategies.EMAXStrategy.EMACrossover.setup')
	@patch('bot.Strategies.EMAXStrategy.EMACrossover.compute_exit_params')
	@patch('bot.Exchanges.Binance.Binance.getSymbolKlines')
	@patch('bot.Engine.OrderManagement.place_sell_order')
	def test_try_exit_order(self, mock_place_sell_order, mock_getSymbolKlines, mock_compute_exit_params, mock_setup_strat):
		mock_compute_exit_params.return_value = dict()
		mock_getSymbolKlines.return_value = pd.DataFrame()
		self.om.try_exit_order(self.eth_order, self.eth_pair)
		self.assertEqual(mock_place_sell_order.call_count, 1)
		self.assertEqual(mock_getSymbolKlines.call_count, 1)
		self.assertEqual(mock_setup_strat.call_count, 1)
		self.assertEqual(mock_compute_exit_params.call_count, 1)

	@patch('bot.Engine.OrderManagement.create_order')
	@patch('bot.Exchanges.Binance.Binance.placeLimitOrder')		
	@patch('bot.Exchanges.Binance.Binance.updateSQLOrderModel')	
	def test_place_sell_order(self, mock_updateSQLOrder, mock_placeLimitOrder, mock_create_order):
		
		exit_params = dict(order_type = self.exchange.ORDER_TYPE_LIMIT)
		
		new_order = deepcopy(self.eth_order)
		new_order.id = 1111
		mock_create_order.return_value = new_order

		order_response = dict(price = self.eth_order.entry_price)
		mock_placeLimitOrder.return_value = order_response

		# Create mock sqlAlchemy session
		mock_session = AlchemyMagicMock()
		
		# create mock orderManagement object with mock db session
		om_mock_database = OrderManagement(
										session=mock_session, 
										bot=self.bot, 
										exchange=self.exchange, 
										strategy=self.strategy
										)

		self.eth_order.is_test = False
		om_mock_database.place_sell_order(exit_params, self.eth_order, self.eth_pair)
		self.assertEqual(mock_session.add.call_count, 1)
		self.assertEqual(new_order.matched_order_id, self.eth_order.id)
		self.assertEqual(self.eth_order.is_closed, True)
		self.assertEqual(self.eth_pair.active, False)

	def test_compute_quantity(self):
		order = self.eth_order
		order.side = 'BUY'
		order.executed_quantity = 4
		exit_quantity = self.om.compute_quantity(order)
		self.assertEqual(exit_quantity, order.executed_quantity)
		
		order.side = 'SELL'
		order.executed_quantity = 4
		order.original_quantity = 8
		self.assertEqual(exit_quantity, order.original_quantity - order.executed_quantity)

if __name__ == "__main__":
	unittest.main()
