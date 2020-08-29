# app/tests/test_order_management.py
import os
import sys

curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)

# DB Tools
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Testing Tools
import unittest
from mock import Mock
from tests.utils import timeit
from tests.helper_functions import get_session
from unittest.mock import patch
from freezegun import freeze_time

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
		# self.df_BTCUSD_1k = pd.read_csv('tests/data/BTCUSD_1m_1k.csv')
		# self.df_BTCUSD_10k = pd.read_csv('tests/data/BTCUSD_1m_10k.csv')
		# self.df_ADABTC_1k = pd.read_csv('./tests/data/ADABTC_1m_1k.csv')
		
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

	# executed after each test
	def tearDown(self):
		pass

	###############
	#### tests ####
	###############

	@patch('bot.Engine.OrderManagement.try_entry_order')
	@patch('bot.Engine.OrderManagement.try_exit_order')
	def test_execute_bot(self, mock_try_exit_order, mock_try_entry_order):
		""""""
		strategy = EMACrossover(5, 30)
		om = OrderManagement(
			bot=self.bot, 
			session=self.session, 
			exchange=self.exchange, 
			strategy=strategy)

		om.execute_bot()

		self.assertEqual(mock_try_entry_order.call_count, 2)
		self.assertEqual(mock_try_exit_order.call_count, 1)


	# def test_SimulatedTrading(self):
	# 	""""""
	# 	session = self.get_session()

	# 	# Create ADABOT
	# 	adabot = Bot(
	# 		name="ada_test_bot",
	# 		quote_asset = 'BTC',
	# 		starting_balance = 1,
	# 		current_balance = 1,
	# 		profit_target = 2,
	# 		test_run=True
	# 	)
	# 	session.add(adabot)
	# 	session.commit()

	# 	pair = Pair(
	# 		bot_id = adabot.id,
	# 		symbol = "ADABTC",
	# 		current_order_id = None
	# 	)

	# 	session.add(pair)
	# 	session.commit()

	# 	pairs_from_bot = adabot.getActivePairs(session)

	# 	self.assertEqual(len(pairs_from_bot), 1)
	# 	self.assertEqual(pairs_from_bot[0].symbol, "ADABTC")

	# 	df = self.df_ADABTC_1k.copy()
	# 	strategy = EMACrossover(5, 30)
	# 	strategy.setup(df)

	# 	PlotData(df, show_plot=True, buy_signals=strategy.getBuySignalsList(),
	# 		plot_indicators= strategy.getIndicators())

	# 	om = OrderManagement(session, adabot, self.exchange, strategy)
	# 	om.try_entry_order = Mock()

	# 	self.exchange.getSymbolKlines = Mock()
	# 	self.exchange.getSymbolKlines.return_value = self.df_ADABTC_1k.copy()
	# 	om.execute_bot()

	# 	self.assertEqual(om.try_entry_order.call_count, 1)

	# 	# 	i = 0
	# 	# 	for i in range(900):
	# 	# 			self.exchange.getSymbolKlines.return_value = self.candlestick_data.head(int(100 + i)).copy()
	# 	# 			ll=len(self.exchange.getSymbolKlines.return_value)
	# 	# 			frozen_time = dt.fromtimestamp(self.candlestick_data['time'][ll]/1000)
	# 	# 			# print("Freezing time to ")
	# 	# 			# print(frozen_time)
	# 	# 			with freeze_time(frozen_time, tz_offset=0):
	# 	# 				# print(datetime.now())
	# 	# 				# print(datetime.timestamp(datetime.now()))
	# 	# 				execute_bot(session, adabot, 'binance_simulation', strategy)
			
	# 	# # self.assertGreater(self.exchange.isValidResponse.call_count, 4)
	# 	# # self.assertLess(self.exchange.isValidResponse.call_count, 20)

				
if __name__ == "__main__":
	unittest.main()
