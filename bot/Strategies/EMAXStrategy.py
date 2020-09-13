from bot.Indicators import AddIndicator # pylint: disable=E0401
import time

class EMACrossover:

	def __init__(self, fast, slow, exchange):
		self.fast = fast
		self.slow = slow
		self.exchange = exchange

	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "sma", "sma_fast", self.fast)
		AddIndicator(self.df, "sma", "sma_slow", self.slow)

	def getIndicators(self):
		return [
			dict(name="sma_fast", title="SMA "+str(self.fast)),
			dict(name="sma_slow", title="SMA "+str(self.slow))
		]

	def checkBuySignal(self, i):
		df = self.df
		if i > 0 and df['sma_fast'][i] >= df['sma_slow'][i] \
			and df['sma_fast'][i-1] < df['sma_slow'][i-1]:
			return True
		return False
	
	def getBuySignalsList(self):
		df = self.df
		length = len(df) - 1
		signals = []
		for i in range(1, length):
			res = self.checkBuySignal(i)
			if res:
				signals.append([df['time'][i], df['close'][i]])

		return signals
	
	def update_open_buy_order(self, order):
		""" Very simple example, can ofc be much more complicated based on price action...."""
		# Binance timestamp is in milliseconds. If open for longer than 2 hours close position.
		if order.timestamp - time.time()*1000 > 2 * 60 * 60 * 1000:
			return True
		else:
			return False

	def update_open_sell_order(self, order):
		""" 
		Limit order example with market order stop-loss built in.
		"""
		update_sell_order = False
		exit_params = dict()

		# Example of limit order with some sort of protection against severe market volatility.
		if order.order_type == self.exchange.ORDER_TYPE_LIMIT:
			i = len(self.df) - 1

			# In case our position goes badly and declines by 5 % under buy price 
			# we place market order to get rid of our position and control our losses.
			if self.df['close'].iloc[i] < 0.95 * order.buy_price:
				update_sell_order = True
				exit_params['order_type'] = self.exchange.ORDER_TYPE_MARKET
				
		return update_sell_order, exit_params

	def compute_exit_params(self, order):
		""" Return initial exit params, again we can make this as complicated as we want. """
		exit_params = dict()
		exit_params['order_type'] = self.exchange.ORDER_TYPE_LIMIT
		exit_params['price'] = order.take_profit_price
		return exit_params
