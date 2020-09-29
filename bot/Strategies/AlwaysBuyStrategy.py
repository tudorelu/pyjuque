from bot.Strategies.BaseStrategy import Strategy

class AlwaysBuyStrategy(Strategy):
	""" Always Buy Strategy:
	Buys when low < close and sells when close > low
	"""

	def __init__(self):
		""" """
		self.minimum_period = 10
	
	def chooseIndicators(self):
		self.indicators = None

	def checkLongSignal(self, i):
		return True
		
	def checkToExitPosition(self, i):
		return True

	def checkShortSignal(self, i):
		return False