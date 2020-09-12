from bot.Indicators import AddIndicator

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
		update_sell_order = False
		exit_params['order_type'] = order.order_type
		if order.order_type == self.exchange.ORDER_TYPE_STOP_LOSS_LIMIT:
			i = len(self.df) - 1
			if df['close'].iloc[i] > order.take_profit_price:
				update_sell_order = True
				exit_params['stop_loss_price'] = order.take_profit_price
				exit_params['take_profit_price'] =  1.02 * order.take_profit_price
				exit_params['side'] = 'SELL'
				exit_params['quantity'] = 

	
	def compute_exit_params(self, order):
		pass