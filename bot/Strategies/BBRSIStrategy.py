from bot.Indicators import AddIndicator # pylint: disable=E0401
import time


class BBRSIStrategy:
	""" Bollinger Bands x RSI Indicator 
		Params
		--
			`rsi_len` = length of RSI
			`bb_len` = length of RBollinger Bands
			`rsi_ob` = Overbought level of RSI	
			`rsi_os` = Oversold level of RSI	
	"""
	def __init__(self, 
		exchange,
		rsi_len = 8, 
		bb_len = 100, 
		rsi_ob = 50, 
		rsi_os = 50,):
		self.rsi_ob = rsi_ob
		self.rsi_os = rsi_os
		self.bb_len = bb_len
		self.rsi_len = rsi_len
		self.exchange = exchange

	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "rsi", "rsi", self.rsi_len)
		AddIndicator(self.df, "lbb", "lbb", self.bb_len)
		AddIndicator(self.df, "ubb", "ubb", self.bb_len)

	def getIndicators(self):
		return [
			dict(name="rsi", title="RSI", yaxis="y3"),
			dict(name="lbb", title="Low Boll", color='gray'),
			dict(name="ubb", title="Upper Boll", color='gray'),
		]

	def checkBuySignal(self, i):
		df = self.df
		if (df["rsi"][i] > self.rsi_os) and \
			(df["rsi"][i-1] <= self.rsi_os) and \
			(df['open'][i] < df["lbb"][i] < df['close'][i]):
			return True
	
		return False
		
	def checkSellSignal(self, i):
		df = self.df
		if (df["rsi"][i] < self.rsi_ob) and \
			(df["rsi"][i-1] >= self.rsi_ob) and \
			(df["close"][i] < df["ubb"][i] < df["open"][i]):
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

	def getSellSignalsList(self):
		df = self.df
		length = len(df) - 1
		signals = []
		for i in range(1, length):
			res = self.checkSellSignal(i)
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
		Trailing stop loss example
		"""
		update_sell_order = False
		exit_params = dict()

		# Example of trailing stops
		if order.order_type == self.exchange.ORDER_TYPE_STOP_LOSS_LIMIT:
			i = len(self.df) - 1
			# basic example of a condition to update trailing stop-loss, can elaborate on this with for example ema crossings and such.
			if self.df['close'].iloc[i] > order.take_profit_price:
				update_sell_order = True
				# set stop loss limit price 4% under current price
				exit_params['price'] = 0.96 * self.df['close'].iloc[i]
				# set stop trigger 2% above limit price.
				exit_params['stop_price'] = 1.02 * exit_params['price']
				# update stop loss again after 2% increase of price
				exit_params['take_profit_price'] =  1.02 * self.df['close'].iloc[i]
				exit_params['order_type'] = self.exchange.ORDER_TYPE_STOP_LOSS_LIMIT
				
		return update_sell_order, exit_params

	def compute_exit_params(self, order):
		""" Return initial exit params, again we can make this as complicated as we want. """
		exit_params = dict()
		exit_params['order_type'] = self.exchange.ORDER_TYPE_STOP_LOSS_LIMIT
		exit_params['price'] = 0.96 * order.price
		exit_params['stop_price'] = 1.02 * exit_params['price']
		exit_params['take_profit_price'] =  1.02 * order.price
		return exit_params