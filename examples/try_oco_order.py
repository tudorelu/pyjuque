
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

def Main():
	exchange = Binance()		
	ctx = Context()
	ctx.prec = 20
	order = OCOOrder(exchange, 'blzbnb', 1, 'SELL', Decimal(0.0064), Decimal(0.0078))

if __name__ == '__main__':
	Main()