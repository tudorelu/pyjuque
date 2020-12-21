import time

import numpy as np
import pandas as pd

from pyti.relative_strength_index import relative_strength_index as pyti_rsi
from pyti.bollinger_bands import lower_bollinger_band as pyti_lbb
from pyti.bollinger_bands import upper_bollinger_band as pyti_ubb
from pyti.on_balance_volume import on_balance_volume as pyti_obv
from pyti.hull_moving_average import hull_moving_average as pyti_hma
from pyti.rate_of_change import rate_of_change as pyti_roc

from pyti.williams_percent_r import williams_percent_r as pyti_wpr

from pyti.ichimoku_cloud import tenkansen, kijunsen, senkou_a, senkou_b

from pyti.simple_moving_average import simple_moving_average as pyti_sma
from pyti.exponential_moving_average import exponential_moving_average as pyti_ema
from pyti.directional_indicators import average_directional_index as pyti_adx
from pyti.standard_deviation import standard_deviation as pyti_stdev
from pyti.moving_average_convergence_divergence import moving_average_convergence_divergence as pyti_macd

from datetime import datetime

from pyjuque.Exchanges.Binance import Binance

def nz(df:pd.DataFrame, y=0):
	""" Replaces NaN values with zeros (or given value) in a series.
	Same as the nz() function of Pinescript """
	return df.fillna(y)

def nz(i:int, y=0):
	""" Same as the nz() function of Pinescript, for ints: 
	Returns y if i is None, or 0 if y is None too """
	if i is None:
		if y is None:
			return 0
		return y
	return i

def timeit(function, text=None, *args):
	''' Used to print the time it takes to run a certain function. '''
	start = time.time()
	ret = function(*args)
	end = time.time()
	if text is None:
		text = function.__name__
	# print(text+": "+str(round(end - start, 4))+" s")
	return ret

def percent_between(a, b):
  return (b - a) / a * 100

def assert_variable_within_range(var, lower, higher):
	assert var >= lower and var <= higher, var.__name__+\
		" outside of permitted range of ["+str(lower)+", "+str(higher)+"]"

def crossover(series1, series2):
	""" Returns a list of bools, each index is true if at that
	point series1 crossed over series2, False otherwise """
	length = len(series1)
	answer = [False]
	if type(series2) == int or type(series2) == float:
		for i in range(1, length):
			if series1[i-1] < series2 and series1[i] > series2:
				answer.append(True)
			else:
				answer.append(False)
	else:
		for i in range(1, length):
			if series1[i-1] < series2[i-1] and series1[i] > series2[i]:
				answer.append(True)
			else:
				answer.append(False)
	
	return answer

def crossunder(series1, series2): 
	""" Returns a list of bools, each index is true if at that
	point series1 crossed under series2, False otherwise """
	length = len(series1)
	answer = [False]
	if type(series2) == int or type(series2) == float:
		for i in range(1, length):
			if series1[i-1] > series2 and series1[i] < series2:
				answer.append(True)
			else:
				answer.append(False)
	else:
		for i in range(1, length):
			if series1[i-1] > series2[i-1] and series1[i] < series2[i]:
				answer.append(True)
			else:
				answer.append(False)
	return answer

def change(series, y=1):
	""" Difference between last value in a series and the yth value previous  """
	ch = []
	for i in range(y):
		ch.append(None)
	for i in range(y, len(series)):
		ch.append(series[i] - series[i-y])
	
	return ch

def donchian_channel(df, period=15):
	length = len(df['close'])
	low = [min(df['low'][max(0, i-period):i+1]) for i in range(length)]
	high = [max(df['high'][max(0, i-period):i+1]) for i in range(length)]
	return low, high

# https://www.tradingview.com/script/ujh3sCzy-RSX-Divergence-SharkCIA/
def rsx(df, period=14, period_buffer=2):
	""" RSX Divergence indicator, from TradingView """
	#	RSX Divergence
  #		Copyright (c) 2019-present, Alex Orekhov (everget)
  # 	Jurik RSX script may be freely distributed under the MIT license.
  #		Source: https://www.tradingview.com/script/ujh3sCzy-RSX-Divergence-SharkCIA/
  
	src = df['close']
	length = len(src)
	
	f8 = 100 * src
	f10 = nz(f8.shift(1, axis = 0))
	v8 = f8 - f10

	f18 = 3 / (period + period_buffer)
	f20 = 1 - f18

	# Pinescript Code:
	# f28 = 0.0
	# f28 := f20 * nz(f28[1]) + f18 * v8
	# Python Code:
	f28 = [0.0]
	for i in range(1, length):
		f28.append(f20 * f28[i-1] + f18 * v8[i])

	# Pinescript Code:
	# f30 = 0.0
	# f30 := f18 * f28 + f20 * nz(f30[1])
	# Python Code:
	f30 = [0.0]
	for i in range(1, length):
		f30.append(f18 * f28[i] + f20 * f30[i-1])
	
	# Pinescript Code:
	# vC = f28 * 1.5 - f30 * 0.5
	# Python Code:
	vC = f30
	for i in range(length):
		vC[i] = f28[i] * 1.5 - f30[i] * 0.5

	f38 = [0.0]
	for i in range(1, length):
		f38.append(f20 * f38[i-1] + f18 * vC[i])

	f40 = [0.0]
	for i in range(1, length):
		f40.append(f18 * f38[i] + f20 * f40[i-1])

	v10 = f38
	for i in range(length):
		v10[i] = f38[i] * 1.5 - f40[i] * 0.5
	
	f48 = [0.0]
	for i in range(1, length):
		f48.append(f20 * f48[i-1] + f18 * v10[i])

	f50 = [0.0]
	for i in range(1, length):
		f50.append(f18 * f48[i] + f20 * f50[i-1])

	v14 = f48
	for i in range(length):
		v14[i] = f48[i] * 1.5 - f50[i] * 0.5

	f58 = [0.0]
	for i in range(1, length):
		f58.append(f20 * f58[i-1] + f18 * abs(v8[i]))

	f60 = [0.0]
	for i in range(1, length):
		f60.append(f18 * f58[i] + f20 * f60[i-1])

	v18 = f58
	for i in range(length):
		v18[i] = f58[i] * 1.5 - f60[i] * 0.5

	f68 = [0.0]
	for i in range(1, length):
		f68.append(f20 * f68[i-1] + f18 * v18[i])

	f70 = [0.0]
	for i in range(1, length):
		f70.append(f18 * f68[i] + f20 * f70[i-1])

	v1C = f68
	for i in range(length):
		v1C[i] = f68[i] * 1.5 - f70[i] * 0.5

	f78 = [0.0]
	for i in range(1, length):
		f78.append(f20 * f78[i-1] + f18 * v1C[i])

	f80 = [0.0]
	for i in range(1, length):
		f80.append(f18 * f78[i] + f20 * f80[i-1])

	v20 = f78
	for i in range(length):
		v20[i] = f78[i] * 1.5 - f80[i] * 0.5

	f88_ = [0.0]
	f90_ = [0.0]
	f88 = [0.0]

	for i in range(1, length):
		if f90_[i-1] == 0.0:
			f90_.append(1)
		else:	
			if f88[i-1] <= f90_[i-1]:
				f90_.append(f88[i-1] + 1)
			else:
				f90_.append(f90_[i-1] + 1)
	
		if f90_[i-1] == 0.0 and period - 1 >= 5:
			f88.append(period - 1)
		else:
			f88.append(5)

	f0 = []
	f90 = []
	for i in range(length):
		# f0 = f88 >= f90_ and f8 != f10 ? 1 : 0
		if f88[i] >= f90_[i] and f8[i] != f10[i]:
			f0.append(1)
		else:
			f0.append(0)
		
		# f90 = f88 == f90_ and f0 == 0 ? 0 : f90_
		if f88[i] == f90_[i] and f0[i] == 0:
			f90.append(0)
		else:
			f90.append(f90_[i])

	v4_ = []
	rsx_ = []
	for i in range(length):
		if f88[i] < f90[i] and v20[i] > 0:
			v4_.append((v14[i] / v20[i] + 1) * 50)
		else:
			v4_.append(50)
		if v4_[i] > 100:
			rsx_.append(100)
		elif v4_[i] < 0:
			rsx_.append(0)
		else:
			rsx_.append(v4_[i])

	return rsx_

def momentum_exhaustion(df, mfi_length=14, ob_level=70, os_level=30, function=rsx, *args):
	# // Momentum Exhaustion Indicator
  #   // Author: @Zeenobit
  #   // Source https://www.tradingview.com/script/GdnsiTe3-Momentum-Exhaustion-Indicator/

	indic = function(df, *args)
	volume = pd.Series(df['volume'])
	high = df['high']
	low = df['low']
	close = df['close']
	hlc3 = (high + low + close) / 3
	change_hlc3 = nz(change(hlc3))
	
	mfp = []
	mfn = []
	mfi = []
	mfp_helper = []
	mfn_helper = []
	length = len(close)

	for i in range(length):
		# mfp = sum(volume * (change(hlc3) < 0 ? 0 : hlc3), mfilength)
		# mfn = sum(volume * (change(hlc3) > 0 ? 0 : hlc3), mfilength)
		if nz(change_hlc3[i]) < 0:
			mfp_helper.append(0)
			mfn_helper.append(volume[i] * hlc3[i])
		else:
			mfp_helper.append(volume[i] * hlc3[i])
			mfn_helper.append(0)
		
		mfp.append(sum(mfp_helper[-mfi_length:]))
		mfn.append(sum(mfn_helper[-mfi_length:]))

		# 	mfi = rsi(mfp, mfn)
		# 	rsi = 100 - 100 / (1 + mfp / mfn)
		mfi.append(100 - 100 / (1 + mfp[i] / mfn[i]))

	ob = []								# Overbought
	os = []								# Oversold
	
	co = crossover(indic, ob_level) 
	cu = crossunder(indic, os_level)
	for i in range(0, length):
		ob.append(co[i] and mfi[i] >= ob_level)
		os.append(cu[i] and mfi[i] <= os_level)
	
	return ob, os

def rsx_momentum_exhaustion(df, mfi_length=14, ob_level=70, os_level=30):
	""" Momentum Exhaustion indicator, using the RSX """
	# // Momentum Exhaustion Indicator
  #   // Author: @Zeenobit
  #   // Source https://www.tradingview.com/script/GdnsiTe3-Momentum-Exhaustion-Indicator/

	rsx_ = rsx(df)
	volume = pd.Series(df['volume'])
	high = df['high']
	low = df['low']
	close = df['close']
	hlc3 = (high + low + close) / 3
	change_hlc3 = nz(change(hlc3))
	
	mfp = []
	mfn = []
	mfi = []
	mfp_helper = []
	mfn_helper = []
	length = len(close)

	for i in range(length):
		# mfp = sum(volume * (change(hlc3) < 0 ? 0 : hlc3), mfilength)
		# mfn = sum(volume * (change(hlc3) > 0 ? 0 : hlc3), mfilength)
		if nz(change_hlc3[i]) < 0:
			mfp_helper.append(0)
			mfn_helper.append(volume[i] * hlc3[i])
		else:
			mfp_helper.append(volume[i] * hlc3[i])
			mfn_helper.append(0)
		
		mfp.append(sum(mfp_helper[-mfi_length:]))
		mfn.append(sum(mfn_helper[-mfi_length:]))

		# 	mfi = rsi(mfp, mfn)
		# 	rsi = 100 - 100 / (1 + mfp / mfn)
		mfi.append(100 - 100 / (1 + mfp[i] / mfn[i]))
  				
	ob = []								# Overbought
	os = []								# Oversold
	
	co = crossover(rsx_, ob_level) 
	cu = crossunder(rsx_, os_level)
	for i in range(0, length):
		ob.append(co[i] and mfi[i] >= ob_level)
		os.append(cu[i] and mfi[i] <= os_level)
	
	return (rsx_, ob, os)

def swing_points(df):
	''' Lagging indicator showing swing points (lagging by 2 candles)

		// Swing Points 
			// Author: @Zeenobit
			// Source: https://www.tradingview.com/script/qnbdnOpc-Swing-Points/
		SL(i) =>
				high[i - 1] > high[i] and high[i] < high[i + 1] and low[i - 1] > low[i] and 
					low[i] < low[i + 1]
		SH(i) =>
				high[i - 1] < high[i] and high[i] > high[i + 1] and low[i - 1] < low[i] and 
					low[i] > low[i + 1]

		SLX(i) =>
				SL(i) and not SH(i + 1)
		SHX(i) =>
				SH(i) and not SL(i + 1)
	'''

	high = df['high']
	low = df['low']
	length = len(high)
	sh = [False]
	sl = [False]
	shx = [False]
	slx = [False]

	for i in range(1, length - 1):
		if high[i - 1] > high[i] and high[i] < high[i + 1] \
			and low[i - 1] > low[i] and low[i] < low[i + 1]:
			sl.append(True)
		else: 
			sl.append(False)

		if high[i - 1] < high[i] and high[i] > high[i + 1] \
			and low[i - 1] < low[i] and low[i] > low[i + 1]:
			sh.append(True)
		else: 
			sh.append(False)
	
	for i in range(1, length - 1):
		if sh[i] and not sl[i+1]:
			shx.append(True)
		else:
			shx.append(False)
		if sl[i] and not sh[i+1]:
			slx.append(True)
		else:
			slx.append(False)
	
	return slx, shx
		
def gann_median(df, period=12, multiplier=1, method="sma"):

	if method == "ema":
		method = pyti_ema
	else:
		method = pyti_sma

	close, open, high, low = df['close'], df['open'], df['high'], df['low']

	df_len = len(df)
	a = []
	b = []
	c = []
	d = []
	lowest = []
	highest = []
	for i in range(df_len):
		if i < period:
			highest.append(min(low[:period]))
			lowest.append(max(high[:period]))
			ocmax = max(close[period - 1], open[period - 1])
			ocmin = min(close[period - 1], open[period - 1])
		else:
			# Append the highest over the last 'period' bars
			highest.append(max(high[:i+1][-period:]))
			lowest.append(min(low[:i+1][-period:]))
			ocmax = max(close[i], open[i])
			ocmin = min(close[i], open[i])

		a.append(highest[i] - ocmax)
		b.append(ocmin - lowest[i])
		c.append(ocmax + a[i] * multiplier)
		d.append(ocmin - b[i] * multiplier)
	
	e = method(c, period)
	f = method(d, period)
	g = [0]

	for i in range(1, df_len):
		if close[i] >= e[i] and close[i-1] < e[i] or \
			close[i] < e[i] and close[i-1] >= e[i]:
			g.append(1)
		elif close[i] >= f[i] and close[i-1] < f[i] or \
			close[i] < f[i] and close[i-1] >= f[i]:
			g.append(0)
		else:
			g.append(g[i-1])
	
	hilo = []
	for i in range(df_len):
		hilo.append(g[i] * f[i] + (1 - g[i]) * e[i])

	return hilo

def rma(source, period):
	# Moving average used in RSI. It is the exponentially 
	# weighted moving average with alpha = 1 / length.
	length = len(source)
	alpha = 1/period
	rma = [source[0]]
	for i in range(1, length):
		rma.append(alpha * source[i] + (1 - alpha) * rma[i-1])

	return rma

def true_range(source, high, low):
	atr = []
	for i in range(len(source)):
		atr.append( \
			max(high[i]-low[i], \
			abs(high[i] - source[i-1]), \
			abs(low[i] - source[i-1])) )
	return atr
	
def average_true_range(source, high, low, period):
	return rma(true_range(source, high, low), period)

def hi_lo_finder(df, left=5, right=5, period=14, mult=0.1, mult_run=0.1):
	""" Trading view indicator identifying pivot highs and lows. """
	'''
		study("My Script")
		// Inputs 
		leftBars     = input(5,   title = 'PP Left Bars')
		rightBars    = input(5,   title = 'PP Right Bars')
		atr_length   = input(14,  title = 'ATR Length')
		atr_mult     = input(0.1, title = 'PP ATR Mult')
		atr_mult_run = input(0.1, title = 'SF ATR Mult')

		// ATR
		atrSPP   = atr(atr_length)
				
		// Pivot High Significant Function
		pivotHighSig(left, right) =>
				pp_ok = true
				atrSPP   = atr(atr_length)
				
				for i = 1 to left
						if (high[right] < high[right+i] + atrSPP * atr_mult)
								pp_ok := false
				for i = 0 to right-1
						if (high[right] < high[i] + atrSPP * atr_mult)
								pp_ok := false
				
				pp_ok ? high[right] : na

		// Pivot Low Significant Function
		pivotLowSig(left, right) =>
				pp_ok = true
				atrSPP   = atr(atr_length)
				
				for i = 1 to left
						if (low[right] > low[right+i] - atrSPP * atr_mult)
								pp_ok := false
				for i = 0 to right-1
						if (low[right] > low[i] - atrSPP * atr_mult)
								pp_ok := false
				
				pp_ok ? low[right] : na


		swh = pivotHighSig(leftBars, rightBars)
		swl = pivotLowSig (leftBars, rightBars)

		swh_cond = not na(swh)

		hprice = 0.0
		hprice := swh_cond ? swh : hprice[1]

		le = false
		le := swh_cond ? true : (le[1] and high > hprice ? false : le[1])

		swl_cond = not na(swl)

		lprice = 0.0
		lprice := swl_cond ? swl : lprice[1]

		se = false
		se := swl_cond ? true : (se[1] and low < lprice ? false : se[1])

		// Calc SFP
		sf_top     = high[1] < hprice[1] and high > hprice + atr_mult_run * atrSPP and close < hprice
		sf_bottom  = low[1]  > lprice[1] and low  < lprice - atr_mult_run * atrSPP and close > lprice

		// Plot PP levels
		plot(lprice, color = color.green,   linewidth = 2)
		plot(hprice, color = color.red, linewidth = 2)

		// Plot SF Signals
		plotshape(sf_top,    location = location.abovebar, color = color.red,   style = shape.arrowdown)
		plotshape(sf_bottom, location = location.belowbar, color = color.green, style = shape.arrowup)

		alertcondition(sf_top,    "SF Top",    "SF Top")
		alertcondition(sf_bottom, "SF Bottom", "SF Bottom")

		//end of this part
	'''

	close = df['close'].tolist()
	high = df['high'].tolist()
	low = df['low'].tolist()
	length = len(df)

	# average true range
	atrSPP = average_true_range(close, high, low)
	
	swh=[]
	for j in range(length):
		if j < right + left:
			swh.append(None)
		else:
			ok = True
			for i in range(1, left + 1): 
				if high[j-right] < high[j-(right+i)] + atrSPP[j] * mult:
					ok = False
				
			for i in range(right):
				if high[j-right] < high[j-i] + atrSPP[j] * mult:
					ok = False
			
			if ok:
				swh.append(high[j-right])
			else:
				swh.append(None)

	swl=[]
	for j in range(length):
		if j < right + left:
			swl.append(None)
		else:
			ok = True
			for i in range(1, left + 1): 
				if low[j-right] > low[j-(right+i)] + atrSPP[j] * mult:
					ok = False
				
			for i in range(right):
				if low[j-right] > low[j-i] + atrSPP[j] * mult:
					ok = False
			
			if ok:
				swl.append(low[j-right])
			else:
				swl.append(None)

	# hprice := swh_cond ? swh : hprice[1]
	hprice = [0.0]
	for i in range(1, length):
		if swh[i]:
			hprice.append(swh[i])
		else:
			hprice.append(hprice[i-1])

	# le := swh_cond ? true : (le[1] and high > hprice ? false : le[1])
	le = [False]
	for i in range(1, length):
		if swh[i]:
			le.append(True)
		elif le[i-1] and high[i] > hprice[i]:
			le.append(False)
		else:
			le.append(le[i-1])

	# lprice := swl_cond ? swl : lprice[1]
	lprice = [0.0]
	for i in range(1, length):
		if swl[i]:
			lprice.append(swl[i])
		else:
			lprice.append(lprice[i-1])

	# se := swl_cond ? true : (se[1] and low < lprice ? false : se[1])
	se = [False]
	for i in range(1, length):
		if swl[i]:
			se.append(True)
		elif se[i-1] and low[i] < lprice[i]:
			se.append(False)
		else:
			se.append(se[i-1])
	
	# Calculate Signals
	# sf_top     = high[1] < hprice[1] and high > hprice + atr_mult_run * atrSPP and close < hprice
	# sf_bottom  = low[1]  > lprice[1] and low  < lprice - atr_mult_run * atrSPP and close > lprice
	sf_top = [False]
	sf_bottom = [False]
	for i in range(1, length):
		sf_top.append((high[i-1] < hprice[i-1] and \
			high[i] > hprice[i] + mult_run * atrSPP[i] and \
			close[i] < hprice[i]))
		sf_bottom.append((low[i-1] > lprice[i-1] and \
			low[i] < lprice[i] - mult_run * atrSPP[i] and \
			close[i] > lprice[i]))
	
	return lprice, hprice, sf_bottom, sf_top

# https://www.tradingview.com/script/4pjBlh4c-Sequentially-Filtered-Moving-Average/
def sequentially_filtered_moving_average(source, period=50):
	""" Custom TV indicator calculating a special moving average """
	'''
		study("Sequentially Filtered Moving Average","SFMA",true)
		length = input(50),src = input(close)
		//----
		sum = 0.
		filt = 0.
		//----
		ma = sma(src,length)
		a = sign(change(ma))
		for i = 0 to length-1
				sum := sum + a[i] 
		alpha = abs(sum) == length ? 1 : 0
		filt := alpha*ma+(1-alpha)*nz(filt[1],ma)
		//----
		css = filt > filt[1] ? #2157f3 : filt < filt[1] ? #ff1100 : na
		plot(filt,"Plot",fixnan(css),3,transp=0)
	'''

	length = len(source)
	ma = pyti_sma(source, period)
	a = [0]
	for i in range(1, length):
		if ma[i] > ma[i-1]:
			a.append(1)
		elif ma[i] < ma[i-1]:
			a.append(-1)
		else:
			a.append(0)
	
	suma = []
	for j in range(length):
		s = 0
		for i in range(period):
			s = s + a[j-i]
		suma.append(s)
	
	filt = [None]
	for i in range(1, length):
		if abs(suma[i]) == period:
			filt.append(ma[i])
		else:
			if filt[i-1] is None:
				filt.append(ma[i])
			else:
				filt.append(filt[i-1])

	return filt

def stochastic(source, high, low, period):
	length = len(source)

	elem_0 = 0
	if high[0] == low[0]:
		elem_0 = 100
	stoch = [elem_0]
	for i in range(1, length):
		num = 0
		if i < period:
			div_by = 1
			if max(high[:(i + 1)]) == min(low[:(i + 1)]):
				div_by = 1
			else:
				div_by = max(high[:(i + 1)]) - min(low[:(i + 1)])
			num = 100 * (source[i] - min(low[:i + 1])) / div_by
		else:
			div_by = 1
			if max(high[(i + 1 - period):(i + 1)]) == min(low[(i + 1 - period):(i + 1)]):
				div_by = 1
			else:
				div_by = max(high[(i + 1 - period): (i + 1)]) - min(low[(i + 1 - period): (i + 1)])
			num = 100 * (source[i] - min(low[(i + 1 - period):(i + 1)])) / div_by
		
		stoch.append(num)
	
	return stoch

# https://www.investopedia.com/articles/trading/07/adx-trend-indicator.asp
def average_directional_index(source, high, low, period):
	length = len(source)
	up = change(high)
	down = [(0 - nz(i)) for i in change(low)]
	trur = average_true_range(source, high, low, period)
	p = []
	m = []
	for i in range(length):
		if nz(up[i]) > down[i] and nz(up[i]) > 0:
			p.append(nz(up[i]))
		else: 
			p.append(0)
		if down[i] > nz(up[i]) and down[i] > 0:
			m.append(down[i])
		else:
			m.append(0)
	p1 = rma(p, period)
	m1 = rma(m, period)
	p2 = [100 * i for i in p1]
	m2 = [100 * i for i in m1]
	plus = [p2[i]/trur[i] for i in range(length)]
	minus = [m2[i]/trur[i] for i in range(length)]

	div = []
	for i in range(length):
		d = plus[i] + minus[i]
		if d == 0:
			d = 1
		div.append(d)

	h = rma([abs(plus[i] - minus[i])/div[i] for i in range(length)], period)
	
	adx = []
	for i in range(length):
		adx.append(100 * h[i])

	return adx

# https://www.tradingview.com/script/UzsROBIg-UCS-S-Stochastic-Pop-and-Drop-Strategy/
def stochastic_pop_drop(df, period=14, adxconf=True, vconf=True, vlen=100, hrange=80, lrange=20):
	
	close = df['close'].tolist()
	high = df['high'].tolist()
	low = df['low'].tolist()
	volume = df['volume'].tolist()
	length = len(df)

	# Trading Bias ??
	tbk = pyti_sma(stochastic(close, high, low, 5 * period), 3)
	tbbull = [(tbk[i] > 50) for i in range(length)]
	tbbear = [(tbk[i] < 50) for i in range(length)]

	# Setup
	sdk = pyti_sma(stochastic(close, high, low, period), 3)
	sdl = [False]
	sds = [False]
	for i in range(1, length):	
		sdl.append(sdk[i] > hrange and sdk[i-1] < hrange)
		sds.append(sdk[i] < lrange and sdk[i-1] > lrange)
	
	# ADX Confirmation
	adx = pyti_adx(close, high, low, period)
	adxc = [(adx[i] < lrange) for i in range(length)]

	# Volume Confirmation
	volma = pyti_sma(volume, vlen)
	volconf = [(volume[i] > volma[i]) for i in range(length)]

	# Long Signals
	#	sl = (steck and vconf) ? volconf == 1 and adxc == 1 and sdl == 1 and tbbull == 1 : 
	# (steck ==1 and vconf != 1) ? adxc == 1 and sdl == 1 and tbbull == 1 : 
	# (steck !=1 and vconf == 1) ? volconf == 1 and sdl == 1 and tbbull == 1 : 
	# sdl == 1 and tbbull == 1
	sl = []
	for i in range(length):
		sl.append(((adxconf and vconf and volconf[i] and adxc[i] and sdl[i] and tbbull[i]) \
			or (adxconf and not vconf and adxc[i] and sdl[i] and tbbull[i]) \
			or (not adxconf and vconf and volconf[i] and sdl[i] and tbbull[i])))
	# Short Signals
	# ss = (steck and vconf) ? volconf == 1 and adxc == 1 and sds == 1 and tbbear == 1 : 
	# (steck ==1 and vconf != 1) ? adxc == 1 and sds == 1 and tbbear == 1 : 
	# (steck !=1 and vconf == 1) ? volconf == 1 and sds == 1 and tbbear == 1 : 
	# sds == 1 and tbbear == 1
	ss = []
	for i in range(length):
		ss.append(((adxconf and vconf and volconf[i] and adxc[i] and sds[i] and tbbear[i]) \
			or (adxconf and not vconf and adxc[i] and sds[i] and tbbear[i]) \
			or (not adxconf and vconf and adxc[i] and sds[i] and tbbear[i])))

	return sdk, sl, ss, adxconf or adx, vconf or volconf

def double_stochastic(df, period1=21, smooth_k1=3, smooth_d1=3, period2=5, smooth_k2=1, smooth_d2=1):
	'''
		study(title="Double Stochastic", shorttitle="DBLStoch")
		length1 = input(21, minval=1), smoothK1 = input(3, minval=1), smoothD1 = input(3, minval=1)
		length2 = input(5, minval=1), smoothK2 = input(1, minval=1), smoothD2 = input(1, minval=1)
		k1 = sma(stoch(close, high, low, length1), smoothK1)
		d1 = sma(k1, smoothD1)
		plot(k1, color=blue)
		plot(d1, color=red)
		k2 = sma(stoch(close, high, low, length2), smoothK2)
		d2 = sma(k2, smoothD2)
		plot(k2, color=orange)

		h0 = hline(80)
		h1 = hline(20)
		fill(h0, h1, color = yellow, transp=90)
	'''
	close = df['close'].tolist()
	high = df['high'].tolist()
	low = df['low'].tolist()

	k1 = pyti_sma(stochastic(close, high, low, period1), smooth_k1)
	d1 = pyti_sma(k1, smooth_d1)

	k2 = pyti_sma(stochastic(close, high, low, period2), smooth_k2)
	d2 = pyti_sma(k2, smooth_d2)

	return k1, d1, k2, d2

def ubb(df, period=21, std=2):
	rolling_mean = df['close'].rolling(period).mean()
	rolling_std = df['close'].rolling(period).std()
	return rolling_mean + (rolling_std * std)

def lbb(df, period=21, std=2):
	rolling_mean = df['close'].rolling(period).mean()
	rolling_std = df['close'].rolling(period).std()
	return rolling_mean - (rolling_std * std)

# TEST THIS
def william_vix_fix_market_bottom(df, pd=22, bbl=20, mult=2.0, lb=50, ph=0.85, lt_lb=40, mt_lb=14, str_=3):
	""" 
		Computes and returns the Williams Vix Fix indicator, together with the 
		upper bollinger band and the higher range. 
		
		If wvf is greater than either the band or the range, that is a  buy signal
	"""
	'''
		study(title="BB VIX FIX Market Bottom", shorttitle="BB VIX FIX Market Bottom", overlay=false)
		//Inputs Tab Criteria.
		pd = input(22, title="LookBack Period Standard Deviation High")
		bbl = input(20, title="Bolinger Band Length")
		mult = input(2.0    , minval=1, maxval=5, title="Bollinger Band Standard Devaition Up")
		lb = input(50  , title="Look Back Period Percentile High")
		ph = input(.85, title="Highest Percentile - 0.90=90%, 0.95=95%, 0.99=99%")
		new = input(false, title="-------Highlight Bars Below Use Original Criteria-------" )
		sbc = input(true, title="Show Highlight Bar if WVF WAS True and IS Now False")
		sbcc = input(false, title="Show Highlight Bar if WVF IS True")
		new2 = input(false, title="-------Highlight Bars Below Use FILTERED Criteria-------" )
		sbcFilt = input(true, title="Show Highlight Bar For Filtered Entry")
		sbcAggr = input(false, title="Show Highlight Bar For AGGRESSIVE Filtered Entry")
		new3 = input(false, title="Check Below to turn All Bars Gray, Then Check the Boxes Above, And your will have Same Colors As VixFix")
		sgb = input(false, title="Check Box To Turn Bars Gray?")
		//Criteria for Down Trend Definition for Filtered Pivots and Aggressive Filtered Pivots
		ltLB = input(40, minval=25, maxval=99, title="Long-Term Look Back Current Bar Has To Close Below This Value OR Medium Term--Default=40")
		mtLB = input(14, minval=10, maxval=20, title="Medium-Term Look Back Current Bar Has To Close Below This Value OR Long Term--Default=14")
		str = input(3, minval=1, maxval=9, title="Entry Price Action Strength--Close > X Bars Back---Default=3")
		//Alerts Instructions and Options Below...Inputs Tab
		new4 = input(false, title="-------------------------Turn On/Off ALERTS Below---------------------" )
		new5 = input(false, title="----To Activate Alerts You HAVE To Check The Boxes Below For Any Alert Criteria You Want----")
		new6 = input(false, title="----You Can Un Check The Box BELOW To Turn Off the WVF Histogram And Just See True/False Alert Criteria----")
		swvf = input(true, title="Show Williams Vix Fix Histogram, Uncheck to Turn Off!")
		sa1 = input(false, title="Show Alert WVF = True?")
		sa2 = input(false, title="Show Alert WVF Was True Now False?")
		sa3 = input(false, title="Show Alert WVF Filtered?")
		sa4 = input(false, title="Show Alert WVF AGGRESSIVE Filter?")

		//Williams Vix Fix Formula
		wvf = ((highest(close, pd)-low)/(highest(close, pd)))*100
		sDev = mult * stdev(wvf, bbl)
		midLine = sma(wvf, bbl)
		lowerBand = midLine - sDev
		upperBand = midLine + sDev
		rangeHigh = (highest(wvf, lb)) * ph

		//Filtered Bar Criteria
		upRange = low > low[1] and close > high[1]
		upRange_Aggr = close > close[1] and close > open[1]
		//Filtered Criteria
		filtered = ((wvf[1] >= upperBand[1] or wvf[1] >= rangeHigh[1]) and (wvf < upperBand and wvf < rangeHigh))
		filtered_Aggr = (wvf[1] >= upperBand[1] or wvf[1] >= rangeHigh[1]) and not (wvf < upperBand and wvf < rangeHigh)

		//Alerts Criteria
		alert1 = wvf >= upperBand or wvf >= rangeHigh ? 1 : 0
		alert2 = (wvf[1] >= upperBand[1] or wvf[1] >= rangeHigh[1]) and (wvf < upperBand and wvf < rangeHigh) ? 1 : 0
		alert3 = upRange and close > close[str] and (close < close[ltLB] or close < close[mtLB]) and filtered ? 1 : 0
		alert4 = upRange_Aggr and close > close[str] and (close < close[ltLB] or close < close[mtLB]) and filtered_Aggr ? 1 : 0

		//Highlight Bar Criteria
		barcolor(sbcAggr and alert4 ? orange : na)
		barcolor(sbcFilt and alert3 ? fuchsia : na)
		barcolor(sbc and ((wvf[1] >= upperBand[1] or wvf[1] >= rangeHigh[1]) and (wvf < upperBand and wvf < rangeHigh)) ? aqua : na)
		barcolor(sbcc and (wvf >= upperBand or wvf >= rangeHigh) ? lime : na)
		barcolor(sgb and close ? gray : na)

		//Coloring Criteria of Williams Vix Fix
		col = wvf >= upperBand or wvf >= rangeHigh ? lime : gray

		//Plots for Williams Vix Fix Histogram and Alerts

		ROC1 = input(title="ROC1", type=integer , defval=10)
		ROC2 = input(title="ROC2", type=integer , defval=5)
		ROC3 = input(title="ROC3", type=integer , defval=1)
		W_ROC1 = input(title="ROC1", type=integer , defval=0.5)
		W_ROC2 = input(title="ROC2", type=integer , defval=0.3)
		W_ROC3 = input(title="ROC3", type=integer , defval=0.2)


		ROC1W = (close - close[1*ROC1]) / close[1*ROC1]
		ROC2W = (close - close[1*ROC2]) / close[1*ROC2]
		ROC3W = (close - close[1*ROC3]) / close[1*ROC3]

		ROC = W_ROC1*ROC1W + W_ROC2*ROC2W + W_ROC3*ROC3W

		scolor =  wvf >= upperBand or wvf >= rangeHigh ? lime : gray

		hline(0)
		plot(ROC, color=scolor, offset = 0, style=columns)
	'''
	assert mult >= 1 and mult <= 5, "mult outside of permitted range of [1, 5]"
	assert lt_lb >= 25 and lt_lb <= 90, "lt_lb outside of permitted range of [25, 90]"
	assert_variable_within_range(mt_lb, 10, 20)
	assert_variable_within_range(str_, 1, 9)

	open = df['open'].tolist()
	close = df['close'].tolist()
	high = df['high'].tolist()
	low = df['low'].tolist()
	length = len(close)

	# Williams Vix Fix Formula
	wvf = [(100 * (max(close[:i+1]) - low[i]) / max(close[:i+1])) for i in range(pd)]
	wvf.extend([(100 * (max(close[i-pd:i+1]) - low[i]) / max(close[i-pd:i+1])) for i in range(pd, length)])
	sDev = mult * pyti_stdev(wvf, bbl)
	midLine = pyti_sma(wvf, bbl)
	lowerBand = midLine - sDev
	upperBand = midLine + sDev
	rangeHigh = [(max(wvf[:i+1]) * ph) for i in range(lb)]
	rangeHigh.extend([(max(wvf[i-lb:i+1]) * ph) for i in range(lb, length)])

	# Filtered Bar Criteria
	upRange = [False]
	upRange_Aggr = [False]
	upRange.extend([low[i] > low[i-1] and close[i] > high[i-1] for i in range(1, length)])
	upRange_Aggr.extend([close[i] > close[i-1] and close[i] > open[i-1] for i in range(1, length)])
	
	# Filtered Criteria
	filtered = [False]
	filtered_Aggr = [False]
	filtered.extend([((wvf[i-1] >= upperBand[i-1] or wvf[i-1] >= rangeHigh[i-1]) and \
		(wvf[i] < upperBand[i] and wvf[i] < rangeHigh[i])) for i in range(1, length)])
	filtered_Aggr.extend([(wvf[i-1] >= upperBand[i-1] or wvf[i-1] >= rangeHigh[i-1]) and \
		not (wvf[i] < upperBand[i] and wvf[i] < rangeHigh[i]) for i in range(1, length)])

	# Alerts Criteria
	alert1 = [wvf[i] >= upperBand[i] or wvf[i] >= rangeHigh[i] for i in range(length)]
	alert2 = [False]
	alert2.extend([(wvf[i-1] >= upperBand[i-1] or wvf[i-1] >= rangeHigh[i-1]) and \
		(wvf[i] < upperBand[i] and wvf[i] < rangeHigh[i]) for i in range(1, length)])
	alert3 = [False for i in range(lt_lb)]
	alert3.extend([upRange[i] and close[i] > close[i - str_] and \
		(close[i] < close[i-lt_lb] or close[i] < close[i - mt_lb]) and filtered[i] \
		for i in range(lt_lb, length)])
	alert4 = [False for i in range(lt_lb)]
	alert4.extend([upRange_Aggr[i] and close[i] > close[i-str_] and \
		(close[i] < close[i-lt_lb] or close[i] < close[i-mt_lb]) and filtered_Aggr[i] \
		for i in range(lt_lb, length)])
	
	return wvf, alert1, alert2, alert3, alert4

def roc(source, roc1=10, roc2=5, roc3=1, wroc1=0.5, wroc2=0.3, wroc3=0.2):
	'''
		ROC1 = input(title="ROC1", type=integer , defval=10)
		ROC2 = input(title="ROC2", type=integer , defval=5)
		ROC3 = input(title="ROC3", type=integer , defval=1)
		W_ROC1 = input(title="ROC1", type=integer , defval=0.5)
		W_ROC2 = input(title="ROC2", type=integer , defval=0.3)
		W_ROC3 = input(title="ROC3", type=integer , defval=0.2)


		ROC1W = (close - close[1*ROC1]) / close[1*ROC1]
		ROC2W = (close - close[1*ROC2]) / close[1*ROC2]
		ROC3W = (close - close[1*ROC3]) / close[1*ROC3]

		ROC = W_ROC1*ROC1W + W_ROC2*ROC2W + W_ROC3*ROC3W

		scolor =  wvf >= upperBand or wvf >= rangeHigh ? lime : gray
	'''
	length = len(source)
	roc1w = [False for i in range(roc1)]
	roc2w = [False for i in range(roc2)]
	roc3w = [False for i in range(roc3)]
	roc1w.extend([(source[i] - source[i - roc1]) / source[i - roc1] for i in range(roc1, length)])
	roc2w.extend([(source[i] - source[i - roc2]) / source[i - roc2] for i in range(roc2, length)])
	roc3w.extend([(source[i] - source[i - roc3]) / source[i - roc3] for i in range(roc3, length)])

	roc = [wroc1 * roc1w[i] + wroc2 * roc2w[i] + wroc3 * roc3w[i] for i in range(length)]
	return roc

# https://www.tradingview.com/script/4VsgFy9h-Stationary-Extrapolated-Levels-Oscillator/
def stationary_extrapolated_levels_oscillator(source, period=56):
	'''
		//@version=4
		study("Stationary Extrapolated Levels Oscillator",shorttitle="SELO",overlay=false)
		length = input(200),src = input(close)
		//----
		y = src - sma(src,length)
		ext = (2*y[length] - y[length*2])/2
		osc = min(max(stoch(y,ext,ext,length*2)/100,0),1)
		//----
		plot(osc,color=osc==1?color.red:osc==0?color.lime:#2196f3,linewidth=2,transp=0)
		hline(0.8,color=#e65100,linewidth=2),hline(0.2,color=#e65100,linewidth=2)
	'''
	length = len(source)
	y = source - pyti_sma(source, period)
	
	ext = [0 for i in range(2*period)]
	ext.extend([(2*y[i-period] - y[i-period*2])/2 for i in range(2*period, length)])
	st = stochastic(y, ext, ext, period * 2) 
	osc = [min(max(st[i]/100, 0), 1) for i in range(length)]
	return osc

# 5m 15m 30m 1h
def regression(source, period=200, diff=0.01):
	"""
		Computes linear regression for the last period values of source,
		and two deviations from it, one above and one below
	"""
	length = len(source)
	source = source[-period:]
	y = range(period)

	middle_line = [None for i in range(length - period)]
	middle_line.extend(np.poly1d(np.polyfit(y, source, 1))(y))
	upper_line = []
	lower_line = []
	for i in range(length):
		if middle_line[i]:
			upper_line.append(middle_line[i] * (1 + diff))
			lower_line.append(middle_line[i] * (1 - diff))
		else:
			upper_line.append(None)
			lower_line.append(None)
	
	return lower_line, middle_line, upper_line

def Main():
	# symbols = ["BTCUSDT", "LTCBTC", "BNBBTC", "NEOBTC", "BNBETH", "BTCUSDT", "ETHUSDT", "WTCBTC", "QTUMBTC", "ZRXBTC", "KNCBTC", "FUNBTC", "LINKBTC", "LINKETH", "XVGBTC", "MTLBTC", "EOSBTC", "ZECBTC", "DASHBTC", "VIBBTC", "TRXBTC", "XRPBTC", "XRPETH", "ENJBTC", "ENJETH", "BNBUSDT", "KMDBTC", "XMRBTC", "AMBBTC", "BATBTC", "ARNBTC", "NEOUSDT", "TNTBTC", "ADABTC", "XLMBTC", "CNDBTC", "LTCUSDT", "WAVESBTC", "ICXBTC", "AIONBTC", "IOSTBTC", "ZILBTC", "ONTBTC", "QTUMUSDT", "XEMBTC", "WPRBTC", "ADAUSDT", "LOOMBTC", "XRPUSDT", "EOSUSDT", "THETABTC", "TUSDUSDT", "XLMUSDT", "NXSBTC", "DATABTC", "ONTUSDT", "TRXUSDT", "ETCUSDT", "VETBTC", "VETUSDT", "DOCKBTC", "POLYBTC", "GOBTC", "PAXUSDT", "RVNBTC", "MITHBTC", "RENBTC", "BTCUSDC", "ETHUSDC", "USDCUSDT", "LINKUSDT", "WAVESUSDT", "BTTUSDT", "ZILUSDT", "FETBTC", "FETUSDT", "BATUSDT", "XMRUSDT", "ZECUSDT", "IOSTUSDT", "CELRBTC", "DASHUSDT", "ENJUSDT", "MATICBNB", "MATICBTC", "MATICUSDT", "ATOMBTC", "ATOMUSDT", "PHBBTC", "ONEBTC", "ONEUSDT", "FTMBTC", "ALGOBTC", "ALGOUSDT", "ERDBTC", "ERDUSDT", "DUSKBTC", "WINUSDT", "TOMOBTC", "TOMOUSDT", "CHZBTC", "BUSDUSDT", "XTZBTC", "XTZUSDT", "RVNUSDT", "ARPABTC", "BCHBTC", "BCHUSDT", "TROYBTC", "TROYUSDT"]

	symbol = "BTCUSDT"
	exchange = Binance()
	df = exchange.getSymbolKlines(symbol, '4h', 1000)
	# df['donc_low'], df['donc_high'] = donchian_channel(df)
	df['ema_50'] = pyti_ema(df['close'].tolist(), 50)
	df['ema_100'] = pyti_ema(df['close'].tolist(), 100)

	print(df)
	# length = len(df['close'])
	# longs = [(df['time'][i], df['close'][i]) 
	# 	for i in range(length) 
	# 		if df['ema_50'][i] > df['ema_100'][i] and df['high'][i] > df['donc_high'][i-1]\
	# 			and (df['ema_50'][i-1] < df['ema_100'][i-1] or df['high'][i-1] <= df['donc_high'][i-2])]
	# shorts = [(df['time'][i], df['close'][i]) 
	# 	for i in range(length) 
	# 		if df['ema_50'][i] < df['ema_100'][i] and df['low'][i] < df['donc_low'][i-1] \
	# 			and (df['ema_50'][i] > df['ema_100'][i] or df['low'][i-1] >= df['donc_low'][i-2])]

	# # These are for plotting
	# plotting_indicators = [
	# 	dict(name="donc_low", title="Lower Donchian Channel ", mode="lines", color='lightblue'),
	# 	dict(name="donc_high", title="Upper Donchian Channel", mode="lines", color='lightblue', fill="tonexty"),
	# 	dict(name="ema_50", title="EMA 50", mode="lines", color='blue'),
	# 	dict(name="ema_100", title="EMA 100", mode="lines", color='red'),
	# ]

	# PlotData(df,
	# 	buy_signals=longs,
	# 	sell_signals=shorts,
	# 	plot_indicators=plotting_indicators,
	# 	plot_title=symbol)


	# pair = timeit(PairModel, "Creating PairModel for "+symbol, symbol_data, df)
	# ob, os = timeit(rsx_momentum_exhaustion, "momentum exhaustion ", df)
	# pyti_adx = timeit(pyti_adx, "pyti adx", close, high, low, 14)
	# my_adx = timeit(average_directional_index, "my ADX function", close, high, low, 14)

	# print(my_adx)
	# print(pyti_adx)

	# st = timeit(stochastic, "my true range function", close, high, low, 14)
	# print(st)

	# df['spd'], df['sl'], df['ss'], ad, vc = stochastic_pop_drop(df)
	# print(df[['date', 'spd', 'sl', 'ss']]) #[-100:-50]

	# df['k1'], df['d1'], df['k2'], df['d2'] = double_stochastic(df)
	# print(df[['date','k1', 'd1', 'k2', 'd2']]) #[-100:-50]

	# df['roc']= roc(df['close'])
	# print(df[['date','roc']]) #[-100:-50]

	# df['wvf'], df['ub'], df['rh']= william_vix_fix_market_bottom(df)
	# print(df[['date','wvf', 'ub', 'rh']][:50])
	# print(df[['date','wvf', 'ub', 'rh']][50:100])
	# print(df[['date','wvf', 'ub', 'rh']][100:150])
	# print(df[['date','wvf', 'ub', 'rh']][150:200])
	# print(df[['date','wvf', 'ub', 'rh']][-350:-300])
	# print(df[['date','wvf', 'ub', 'rh']][-300:-250])
	# print(df[['date','wvf', 'ub', 'rh']][-250:-200])
	# print(df[['date','wvf', 'ub', 'rh']][-200:-150])
	# print(df[['date','wvf', 'ub', 'rh']][-150:-100])
	# print(df[['date','wvf', 'ub', 'rh']][-100:-50])
	# print(df[['date','wvf', 'ub', 'rh']][-50:])

	# lr, mr, ur = regression(df['close'])
     
	# plt.figure(figsize=(8,6))
	# plt.grid(True)
	# plt.plot(df['close'])
	# plt.plot(lr, '--', color='r')
	# plt.plot(mr, '--', color='r')
	# plt.plot(ur, '--', color='r')
	# plt.show()

	# tr = timeit(true_range, "my true range function", close, high, low)
	#atr = timeit(average_true_range, "my true range function", close, high, low, 14)
	# rma_ = timeit(rma, "rma function", close, 14)

	# print(my_adx)
	# print(mytr)
	# df['atr_high'], df['atr_low'], df['atr_top'], df['atr_bottom'] = \
	# 	timeit(hi_lo_finder, "ATR hi lo top bottom", df)
	# print(df[['date', 'atr_high', 'atr_low', 'atr_top', 'atr_bottom']][-100:-50])

	#df['sfma'] = timeit(sequentially_filtered_moving_average, "get SFMA", df['close'].tolist())

if __name__ == "__main__":
	Main()
