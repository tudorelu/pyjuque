from pyjuque.Indicators import AddIndicator

class SimpleTwoStrategy:
	"""
	src = input(defval=close, title="Source")

	per = input(defval=100, minval=1, title="Sampling Period")

	mult = input(defval=5.5, minval=1.7, title="Range Multiplier")

	smoothrng(x, t, m)=>
	    wper      = (t*2) - 1
	    avrng     = ema(abs(x - x[1]), t)
	    smoothrng = ema(avrng, wper)*m
	    smoothrng
	smrng = smoothrng(src, per, mult)

	"""

	def __init__(self, per=100, mult=5.5):
		""" 
		per = input(defval=100, minval=1, title="Sampling Period")
		mult = input(defval=5.5, minval=1.7, title="Range Multiplier")
		"""
		self.per=per
		self.mult=mult

	
	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "smoothrng", "smoothrng_"+str(self.per), self.per, self.mult)


	def getIndicators(self):
		return [
			dict(name="smoothrng_"+str(self.per), title="SMOOTHRNG", yaxis="y3"),
		]

	def checkBuySignal(self, i):
		# df = self.df
		# if df["low"][i] < df["close"][i]:
		# 	return True
	
		return False
		
	def checkSellSignal(self, i):
		# df = self.df
		# if df["close"][i] > df["low"][i]:
		# 	return True
	
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