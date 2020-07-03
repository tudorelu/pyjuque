# app/tests/test_basic.py

import os
import unittest

import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
# Import all Created exchanges here
from bot.Exchanges.Binance import Binance
from bot.Indicators import AddIndicator, INDICATOR_DICT
from tests.utils import timeit
from pandas import DataFrame

import pandas

import json

class PytiIndicatorsTests(unittest.TestCase):
	############################
	#### setup and teardown ####
	############################

	# executed prior to each test
	def setUp(self):	
		self.df_1k = pandas.read_csv('tests/data/BTCUSD_1m_1k.csv')
		self.df_10k = pandas.read_csv('tests/data/BTCUSD_1m_10k.csv')
		
	# executed after each test
	def tearDown(self):
		pass

	###############
	#### tests ####
	###############
	def test_AddCredentials(self):
		for key in INDICATOR_DICT.keys():
			ret, time_5 = timeit(AddIndicator, False, self.df_1k, key, key, 5)
			ret, time_50 = timeit(AddIndicator, False, self.df_1k, key, key, 50)
			ret, time_500 = timeit(AddIndicator, False, self.df_1k, key, key, 500)
			print("Times for calculating "+key+" \n on a dataframe with 1k rows:")
			print("Period 5: ", round(time_5, 4), "| Period 50: ", round(time_50, 4), \
				"| Period 500: ", round(time_500, 4))

			ret, time_5 = timeit(AddIndicator, False, self.df_10k, key, key, 5)
			ret, time_50 = timeit(AddIndicator, False, self.df_10k, key, key, 50)
			ret, time_500 = timeit(AddIndicator, False, self.df_10k, key, key, 500)
			print(" and on a dataframe with 10k rows:")
			print("Period 5: ", round(time_5, 4), "| Period 50: ", round(time_50, 4), \
				"| Period 500: ", round(time_500, 4), "\n")

if __name__ == "__main__":
	unittest.main()
