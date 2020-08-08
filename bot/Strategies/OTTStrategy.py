from bot.Indicators import AddIndicator

class OTTStrategy:
	"""
		//@version=4
		// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
		// Â© KivancOzbilgic

		//created by: @Anil_Ozeksi
		//developer: ANIL Ã–ZEKÅžÄ°
		//author: @kivancozbilgic

		study("Optimized Trend Tracker","OTT", overlay=true)
		src = input(close, title="Source")
		pds=input(1, "OTT Period", minval=1)
		percent=input(0.1, "OTT Percent", type=input.float, step=0.1, minval=0)

		showsupport = input(title="Show Support Line?", type=input.bool, defval=true)
		showsignalsk = input(title="Show Support Line Crossing Signals?", type=input.bool, defval=true)
		showsignalsc = input(title="Show Price/OTT Crossing Signals?", type=input.bool, defval=false)
		highlight = input(title="Show OTT Color Changes?", type=input.bool, defval=true)
		showsignalsr = input(title="Show OTT Color Change Signals?", type=input.bool, defval=false)
		highlighting = input(title="Highlighter On/Off ?", type=input.bool, defval=true)


		alpha=2/(pds+1)
		ud1=src>src[1] ? src-src[1] : 0
		dd1=src<src[1] ? src[1]-src : 0

		UD=sum(ud1,9)
		DD=sum(dd1,9)
		CMO=(UD-DD)/(UD+DD)
		k= abs(CMO)
		Var=0.0
		Var:=(alpha*k*src)+(1-alpha*k)*nz(Var[1])

		fark=Var*percent*0.01
		longStop = Var - fark
		longStopPrev = nz(longStop[1], longStop)
		longStop := Var > longStopPrev ? max(longStop, longStopPrev) : longStop
		shortStop =  Var + fark
		shortStopPrev = nz(shortStop[1], shortStop)
		shortStop := Var < shortStopPrev ? min(shortStop, shortStopPrev) : shortStop
		dir = 1
		dir := nz(dir[1], dir)
		dir := dir == -1 and Var > shortStopPrev ? 1 : dir == 1 and Var < longStopPrev ? -1 : dir
		MT = dir==1 ? longStop: shortStop
		OTT=Var>MT ? MT*(200+percent)/200 : MT*(200-percent)/200 

		plot(showsupport ? Var : na, color=#0585E1, linewidth=2, title="Support Line")
		OTTC = highlight ? OTT[2] > OTT[3] ? color.green : color.red : #B800D9 
		pALL=plot(nz(OTT[2]), color=OTTC, linewidth=2, title="OTT", transp=0)
		alertcondition(cross(OTT[2], OTT[3]), title="Color ALARM", message="OTT Has Changed Color!")
		alertcondition(crossover(OTT[2], OTT[3]), title="GREEN ALERT", message="OTT GREEN BUY SIGNAL!")
		alertcondition(crossunder(OTT[2], OTT[3]), title="RED ALERT", message="OTT RED SELL SIGNAL!")
		alertcondition(cross(Var, OTT[2]), title="Cross Alert", message="OTT - Support Line Crossing!")
		alertcondition(crossover(Var, OTT[2]), title="Crossover Alarm", message="Support Line BUY SIGNAL!")
		alertcondition(crossunder(Var, OTT[2]), title="Crossunder Alarm", message="Support Line SELL SIGNAL!")
		alertcondition(cross(src, OTT[2]), title="Price Cross Alert", message="OTT - Price Crossing!")
		alertcondition(crossover(src, OTT[2]), title="Price Crossover Alarm", message="PRICE OVER OTT - BUY SIGNAL!")
		alertcondition(crossunder(src, OTT[2]), title="Price Crossunder Alarm", message="PRICE UNDER OTT - SELL SIGNAL!")
		buySignalk = crossover(Var, OTT[2])

		plotshape(buySignalk and showsignalsk ? OTT*0.995 : na, title="AL", text="AL", location=location.absolute, style=shape.labelup, size=size.tiny, color=color.green, textcolor=color.white, transp=0)
		sellSignallk = crossunder(Var, OTT[2])
		plotshape(sellSignallk and showsignalsk ? OTT*1.005 : na, title="SELL", text="SELL", location=location.absolute, style=shape.labeldown, size=size.tiny, color=color.red, textcolor=color.white, transp=0)
		buySignalc = crossover(src, OTT[2])


		plotshape(buySignalc and showsignalsc ? OTT*0.995 : na, title="BUY", text="BUY", location=location.absolute, style=shape.labelup, size=size.tiny, color=#0F18BF, textcolor=color.white, transp=0)
		sellSignallc = crossunder(src, OTT[2])
		plotshape(sellSignallc and showsignalsc ? OTT*1.005 : na, title="SELL", text="SELL", location=location.absolute, style=shape.labeldown, size=size.tiny, color=color.red, textcolor=color.white, transp=0)
		mPlot = plot(ohlc4, title="", style=plot.style_circles, linewidth=0,display=display.none)
		longFillColor = highlighting ? (Var>OTT ? color.green : na) : na
		shortFillColor = highlighting ? (Var<OTT ? color.red : na) : na
		fill(mPlot, pALL, title="UpTrend Highligter", color=longFillColor)
		fill(mPlot, pALL, title="DownTrend Highligter", color=shortFillColor)
		buySignalr = crossover(OTT[2], OTT[3])

		plotshape(buySignalr and showsignalsr ? OTT*0.995 : na, title="BUY", text="BUY", location=location.absolute, style=shape.labelup, size=size.tiny, color=color.green, textcolor=color.white, transp=0)
		sellSignallr = crossunder(OTT[2], OTT[3])

		plotshape(sellSignallr and showsignalsr ? OTT*1.005 : na, title="SELL", text="SELL", location=location.absolute, style=shape.labeldown, size=size.tiny, color=color.red, textcolor=color.white, transp=0)
	"""

	def __init__(self, pds=1, percent=0.1):
		""" 
		pds=input(1, "OTT Period", minval=1)
		percent=input(0.1, "OTT Percent", type=input.float, step=0.1, minval=0)
		"""
		self.pds = pds
		self.percent = percent
	
	def setup(self, df):
		self.df = df
		AddIndicator(self.df, "ott", ["var", "ott"], self.pds, self.percent)

	def getIndicators(self):
		return [
			dict(name="ott", title="OTT", color="green"),
			dict(name="var", title="Var", color="blue")
		]

	def checkBuySignal(self, i):
		# buySignalk = crossover(Var, OTT[2])
		df = self.df
		if i >= 3 and \
			df["var"][i-1] < df["ott"][i-3] and \
			df["var"][i] > df["ott"][i-2]:
			return True

		return False
		
	def checkSellSignal(self, i):
		# sellSignallk = crossunder(Var, OTT[2])
		df = self.df
		if i >= 3 and \
			df["var"][i-1] > df["ott"][i-3] and \
			df["var"][i] < df["ott"][i-2]:
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