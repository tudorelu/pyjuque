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

	order = OCOOrder(exchange, 'ethusdt', 0.05, 'SELL', Decimal(367), Decimal(368), verbose=2)
	order.start()


if __name__ == '__main__':
	Main()