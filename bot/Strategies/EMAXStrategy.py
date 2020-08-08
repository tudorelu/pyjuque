from bot.Indicators import AddIndicator

class EMACrossover:

	def __init__(self, fast, slow):
		self.fast = fast
		self.slow = slow

	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "sma", "sma_fast", self.fast)
		AddIndicator(self.df, "sma", "sma_slow", self.slow)

	def evaluate(self, i):
		df = self.df
		if i > 0 and df['sma_fast'][i] >= df['sma_slow'][i] \
			and df['sma_fast'][i-1] < df['sma_slow'][i-1]:
			return df['close'][i]
		return False
	
	def getSignalsList(self):
		df = self.df
		length = len(df) - 1
		signals = []
		for i in range(1, length):
			res = self.evaluate(i)
			if res:
				signals.append([df['time'][i], df['close'][i]])

		return signals
