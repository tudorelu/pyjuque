
from time import time

def timeit(function, text=None, *args):
	''' Used to print the time it takes to run a certain function. '''
	start = time()
	ret = function(*args)
	end = time()
	if text is not False:
		if text is None or text == "":
			text = function.__name__+" took "
		print(text+str(round(end - start, 4))+" s")
	return ret, end - start

import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from bot.Exchanges.Binance import Binance

exchange = Binance()
df = exchange.getSymbolKlines("BTCUSDT", "1m", 1000)
df.to_csv('tests/data/BTCUSD_1m_1k.csv')