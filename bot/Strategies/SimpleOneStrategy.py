from bot.Indicators import AddIndicator

class SimpleOneStrategy:
	"""
	///ShivaGuru
	//@version=3
	//author: muhammetta

	study("3 RSI PERIODS ", shorttitle="3 RSI")
	src = input(ohlc4, title="Source")

	RSIperiod3 = input(3,title="RSIperiod 3")
	RSIperiod8 = input(8,title="RSIperiod 8")
	RSIperiod34 = input(34,title="RSIperiod 34")


	RSI3 = rsi(src, RSIperiod3)
	RSI8 = rsi(src, RSIperiod8)
	RSI34 = rsi(src, RSIperiod34)


	plot(RSI3, title= "RSI 3", color=green, linewidth=2)
	plot(RSI8,  title= "RSI 8", color=orange, linewidth=2)
	plot(RSI34, title= "RSI 34", color=navy, linewidth=2)

	hline(100,title='100 line', color=red, linewidth=1)
	hline(50,title='50 line', color=black, linewidth=2)
	hline(0,title='0 line', color=green, linewidth=1)

	"""

	def __init__(self, rsi_len_1=3, rsi_len_2=8, rsi_len_3=34):
		""" 	
		src = input(ohlc4, title="Source")

		RSIperiod3 = input(3,title="RSIperiod 3")
		RSIperiod8 = input(8,title="RSIperiod 8")
		RSIperiod34 = input(34,title="RSIperiod 34")"""
		self.rsi_len_1=rsi_len_1
		self.rsi_len_2=rsi_len_2 
		self.rsi_len_3=rsi_len_3

	
	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "rsi", "rsi_"+str(self.rsi_len_1), self.rsi_len_1)
		AddIndicator(self.df, "rsi", "rsi_"+str(self.rsi_len_2), self.rsi_len_2)
		AddIndicator(self.df, "rsi", "rsi_"+str(self.rsi_len_3), self.rsi_len_3)


	def getIndicators(self):
		return [
			dict(name="rsi_"+str(self.rsi_len_1), title="RSI "+str(self.rsi_len_1), yaxis="y3"),
			dict(name="rsi_"+str(self.rsi_len_2), title="RSI "+str(self.rsi_len_2), yaxis="y3"),
			dict(name="rsi_"+str(self.rsi_len_3), title="RSI "+str(self.rsi_len_3), yaxis="y3")
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