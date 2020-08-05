from bot.Indicators import AddIndicator

class AlwaysBuyStrategy:
	""" Always Buy Strategy:
	Buys when low < close and sells when close > low
	"""

	def __init__(self):
		""" """
	
	def setup(self, df):
		self.df = df

	def getIndicators(self):
		return []

	def checkBuySignal(self, i):
		df = self.df
		if df["low"][i] < df["close"][i]:
			return True
	
		return False
		
	def checkSellSignal(self, i):
		df = self.df
		if df["close"][i] > df["low"][i]:
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