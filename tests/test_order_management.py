# app/tests/test_order_management.py
import os
import sys

curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

# DB Tools
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Testing Tools
import unittest
from mock import Mock
from tests.utils import timeit
from unittest.mock import patch
from freezegun import freeze_time

# Other Tools
import json
import pandas as pd
import datetime as dt

# Pyjuque Modules
from bot.Exchanges.Binance import Binance
from bot.Strategies.EMAXStrategy import EMACrossover
from bot.Engine import backtest, OrderManagement, Order, Pair, Bot, Base
from bot.Plotter import PlotData

class OrderManagementTests(unittest.TestCase):
	############################
	#### setup and teardown ####
	############################

	# executed prior to each test
	def setUp(self):	
		self.exchange = Binance()
		self.df_BTCUSD_1k = pd.read_csv('tests/data/BTCUSD_1m_1k.csv')
		self.df_BTCUSD_10k = pd.read_csv('tests/data/BTCUSD_1m_10k.csv')
		self.df_ADABTC_1k = pd.read_csv('./tests/data/ADABTC_1m_1k.csv')       
				
		
	# executed after each test
	def tearDown(self):
		pass


	##########################
	#### helper functions ####
	##########################
	def get_session(self, path='sqlite:///'):
		some_engine = create_engine(path, echo=False)
		Base.metadata.create_all(some_engine)
		Session = sessionmaker(bind=some_engine)
		session = Session()
		return session


	###############
	#### tests ####
	###############

	def test_BotCreation(self):
		session = self.get_session()
		self.assertEqual(len(session.query(Bot).all()), 0)
		
		# Create ADABOT
		adabot = Bot(
			name="ada_test_bot",
			quote_asset = 'BTC',
			starting_balance = 1,
			current_balance = 1,
			profit_target = 2,
			test_run=True
		)
		session.add(adabot)
		session.commit()
		self.assertEqual(len(session.query(Bot).all()), 1)

		adabot = session.query(Bot).filter_by(name="ada_test_bot").first()
		self.assertEqual(adabot.test_run, True)
		self.assertEqual(adabot.quote_asset, 'BTC')
		self.assertEqual(adabot.starting_balance, 1)
		self.assertEqual(adabot.current_balance, 1)
		self.assertEqual(adabot.profit_target, 2)
		self.assertEqual(adabot.profit_loss, 100)
		

	def test_SimulatedTrading(self):
		""""""
		session = self.get_session()

		# Create ADABOT
		adabot = Bot(
			name="ada_test_bot",
			quote_asset = 'BTC',
			starting_balance = 1,
			current_balance = 1,
			profit_target = 2,
			test_run=True
		)
		session.add(adabot)
		session.commit()

		pair = Pair(
			bot_id = adabot.id,
			symbol = "ADABTC",
			current_order_id = None
		)

		session.add(pair)
		session.commit()

		pairs_from_bot = adabot.getActivePairs(session)

		self.assertEqual(len(pairs_from_bot), 1)
		self.assertEqual(pairs_from_bot[0].symbol, "ADABTC")

		df = self.df_ADABTC_1k.copy()
		strategy = EMACrossover(5, 30)
		strategy.setup(df)

		PlotData(df, show_plot=True, buy_signals=strategy.getBuySignalsList(),
			plot_indicators= strategy.getIndicators())

		om = OrderManagement(session, adabot, self.exchange, strategy)
		om.try_entry_order = Mock()

		self.exchange.getSymbolKlines = Mock()
		self.exchange.getSymbolKlines.return_value = self.df_ADABTC_1k.copy()
		om.execute_bot()

		self.assertEqual(om.try_entry_order.call_count, 1)

		# 	i = 0
		# 	for i in range(900):
		# 			self.exchange.getSymbolKlines.return_value = self.candlestick_data.head(int(100 + i)).copy()
		# 			ll=len(self.exchange.getSymbolKlines.return_value)
		# 			frozen_time = dt.fromtimestamp(self.candlestick_data['time'][ll]/1000)
		# 			# print("Freezing time to ")
		# 			# print(frozen_time)
		# 			with freeze_time(frozen_time, tz_offset=0):
		# 				# print(datetime.now())
		# 				# print(datetime.timestamp(datetime.now()))
		# 				execute_bot(session, adabot, 'binance_simulation', strategy)
			
		# # self.assertGreater(self.exchange.isValidResponse.call_count, 4)
		# # self.assertLess(self.exchange.isValidResponse.call_count, 20)

				
if __name__ == "__main__":
	unittest.main()
