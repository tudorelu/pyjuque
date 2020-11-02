# app/tests/test_basic.py

import os
import sys
import unittest

curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)

# Import all Created exchanges here
from pyjuque.Exchanges.Binance import Binance
from tests.utils import timeit
from pandas import DataFrame

class BinanceTests(unittest.TestCase):
  
	############################
	#### setup and teardown ####
	############################

	# executed prior to each test
	def setUp(self):
		self.exchange = Binance()
		self.exchange.addCredentials("invalid_api_key", "invalid_secret_key")

	# executed after each test
	def tearDown(self):
		pass

	###############
	#### tests ####
	###############
	def test_AddCredentials(self):
		self.assertEqual(self.exchange.has_credentials, True, "Exchange should have credentials now.")

	def test_GetAccountData(self):
		acct_data = self.exchange.getAccountData()
		assert isinstance(acct_data, dict), "getAccountData should return a dict"
		assert acct_data.__contains__('code'), \
			"Response should contain an error since the api-secret key pair \
				is invalid."

	def test_GetTradingSymbols(self):
		trading_symbols = self.exchange.getTradingSymbols()
		assert isinstance(trading_symbols, list), "getTradingSymbols should return a list"

	def test_GetSymbolKlines(self):
		
		limit = 1000
		timeframe = "1m"
		symbol = "BTCUSDT"

		df = self.exchange.getSymbolKlines(symbol, timeframe, limit)
		assert isinstance(df, DataFrame), "getSymbolKlines should return a dataframe"

		length = len(df) - 1
		assert length + 1 == limit, "there should be " + str(limit) \
			+ " entries in the dataframe, not "+str(length + 1)

		for x in ['open', 'high', 'low', 'close', 'volume', 'time', 'date']:
			assert x in df.columns, \
				x+" should be a column in the Candlestick dataframe"
		
		for i in range(1, length):
			assert (df['close'][i] <= df['high'][i] and \
				df['close'][i] >= df['low'][i] and \
				df['open'][i] <= df['high'][i] and \
				df['open'][i] >= df['low'][i]), \
					"high should not be less than close nor open, and " \
					+ "low should not be greater than either of them "


if __name__ == "__main__":
  	
	print("\nRunning tests for the Binance exchange.")
	unittest.main()
