
import os
import sys

curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)

# Import all Created exchanges here
from bot.Exchanges.Binance import Binance
from bot.Engine.OCOOrder import OCOOrder 

from decimal import Decimal, Context
from uuid import uuid4
from pprint import pprint

def Main():

	exchange = Binance(get_credentials_from_env=True)

	ctx = Context()
	ctx.prec = 20

	order = OCOOrder(exchange, 'sushiusdt', 10, 'SELL', Decimal(2), Decimal(2.45))
	order.start()

	# order_id = uuid4()
	# response = exchange.getAllOrders('sushiusdt', 10)
	# response = order.exchange.placeTakeProfitLimitOrder(
	# 	symbol=order.symbol, amount=order.quantity, side=order.side, 
	# 	price=order.take_profit, stop_price=order.sl_plus_two_3_diff, 
	# 	custom_id=order_id)
	# response = exchange.cancelOrder(
	# 	symbol='SUSHIUSDT', 
	# 	order_id='03df1541-d417-41d8-93b0-3a9fb44861fe', 
	# 	is_custom_id=True)
	# pprint(response)
	# order = OCOOrder(exchange, 'sushiusdt', 10, 'SELL', Decimal(2.78), Decimal(3))

if __name__ == '__main__':
	Main()