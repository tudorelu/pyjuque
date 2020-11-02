import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pprint import pprint
from bot.Engine.OrderBook import OrderBook

if __name__ == '__main__':
	ob = OrderBook(symbols=['BTCUSDT'])

	ob.startOrderBook()
	time.sleep(10)
	ordb = ob.getOrderBook()
	pprint(ordb)
	time.sleep(3)
	ordb = ob.getOrderBook()
	pprint(ordb)
	time.sleep(3)
	ob.stopOrderBook()