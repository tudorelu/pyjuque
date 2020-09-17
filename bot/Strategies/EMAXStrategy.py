from bot.Indicators.Indicators import AddIndicator

class EMACrossover:

	def __init__(self, fast, slow):
		self.fast = fast
		self.slow = slow
		self.minimum_period = max(self.fast, self.slow) + 5

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
