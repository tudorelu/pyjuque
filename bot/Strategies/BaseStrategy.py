from abc import ABC, abstractmethod 

class BaseStrategy(ABC):
	""" Base Strategy Class """
	def __init__(self):
			
			# Minumum period needed for indicators to be calculated
			self.minimum_period = 100
			
			# Timeframe of Strategy for indicators to be calculated
			self.default_timeframe = ''

			# In case of multiple timeframes
			self.timeframes = []

	def setup(self, df):
			pass

	def getIndicators(self):
			pass

	def checkBuySignal(self, i):
			pass
		
	def checkSellSignal(self, i):
			pass

	def getBuySignalsList(self):
			pass

	def getSellSignalsList(self):
			pass