from pyjuque.Indicators import AddIndicator # pylint: disable=E0401
from pyjuque.Strategies.BaseStrategy import Strategy

class BBRSIStrategy(Strategy):
	""" Bollinger Bands x RSI Indicator
		Params
		--
			`rsi_len` = length of RSI
			`bb_len` = length of RBollinger Bands
			`rsi_ob` = Overbought level of RSI
			`rsi_os` = Oversold level of RSI
	"""
	def __init__(self,
		rsi_len = 8,
		bb_len = 100,
		rsi_ob = 50,
		rsi_os = 50,):

		self.rsi_ob = rsi_ob
		self.rsi_os = rsi_os
		self.bb_len = bb_len
		self.rsi_len = rsi_len
		self.minimum_period = 100

		self.chooseIndicators()

	def chooseIndicators(self):
		self.indicators = (dict(indicator_name = 'rsi', col_name = 'rsi', rsi_len = self.rsi_len),
						   dict(indicator_name = 'lbb', col_name = 'lbb', rsi_len = self.bb_len),
						   dict(indicator_name = 'ubb', col_name = 'ubb', rsi_len = self.bb_len))

	def checkLongSignal(self, i):
		df = self.df
		if (df["rsi"][i] > self.rsi_ob) and \
			(df["rsi"][i-1] <= self.rsi_ob) and \
			(df["open"][i] < df["lbb"][i] < df["close"][i]):
			return True
		return False

	def checkShortSignal(self, i):
		return False

	def checkToExitLongPosition(self, i):
		df = self.df
		if (df["rsi"][i] < self.rsi_ob) and \
			(df["rsi"][i-1] >= self.rsi_ob) and \
			(df["close"][i] < df["ubb"][i] < df["open"][i]):
			return True
		return False

