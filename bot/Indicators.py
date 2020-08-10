# TI & TA
from pyti.smoothed_moving_average import smoothed_moving_average as pyti_smmoothed_ma
from pyti.simple_moving_average import simple_moving_average as pyti_sma 
from pyti.bollinger_bands import lower_bollinger_band as pyti_lbb
from pyti.bollinger_bands import upper_bollinger_band as pyti_ubb
from pyti.accumulation_distribution import accumulation_distribution as acd
from pyti.aroon import aroon_up
from pyti.aroon import aroon_down

from pyti.rate_of_change import rate_of_change as roc
from pyti.relative_strength_index import relative_strength_index as pyti_rsi
from pyti.commodity_channel_index import commodity_channel_index 
from pyti.exponential_moving_average import exponential_moving_average as pyti_ema

from traceback import print_exc

def cci(df, period):
	return commodity_channel_index(df['close'].tolist(), df['high'].tolist(), df['low'].tolist(), period)

def smoothrng(df, period, multiplier):
	"""
	smoothrng(x, t, m)=>
	    wper      = (t*2) - 1
	    avrng     = ema(abs(x - x[1]), t)
	    smoothrng = ema(avrng, wper)*m
	    smoothrng
	smrng = smoothrng(src, per, mult)
	"""

	wper = 2 * period - 1
	
	abs_change = []
	prev_row = None
	for i, row in df.iterrows():
		if i == 0:
			abs_change.append(0)
		else:
			abs_change.append(abs(row['close'] - prev_row['close']))
		prev_row = row	
			
	avrng = ema(abs_change, period)
	smoothrng = ema(avrng, wper) * multiplier

	return smoothrng

def nz(df, y=0):
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

def ott(df, pds, percent):
	""" 
	alpha=2/(pds+1)
	ud1=src>src[1] ? src-src[1] : 0
	dd1=src<src[1] ? src[1]-src : 0
	"""
	src = df['close'].tolist()
	alpha = 2 / (pds+1)
	index = 0
	ud1 = []
	dd1 = []
	prev_elem = None
	for elem in src:
		if index == 0:
			ud1.append(0)
			dd1.append(0)
		else:
			if elem > prev_elem:
				ud1.append(elem-prev_elem)
			else:
				ud1.append(0)
			
			if elem < prev_elem:
				dd1.append(prev_elem-elem)
			else:
				dd1.append(0)

		index+=1
		prev_elem = elem

	""" 
		UD=sum(ud1,9)
		DD=sum(dd1,9)
		CMO=(UD-DD)/(UD+DD)
		k= abs(CMO)
	"""
	len_ud1 = len(ud1)
	len_dd1 = len(dd1)
	UD = [sum(ud1[i-9:i]) if i >= 9 else sum(ud1[:i]) for i in range(len_ud1+1)]
	DD = [sum(dd1[i-9:i]) if i >= 9 else sum(dd1[:i]) for i in range(len_dd1+1)]
	# print(ud1[-4:])
	# print(UD[-4:])
	# print(dd1[-4:])
	# print(DD[-4:])

	CMO = []
	for i in range(len(DD)):
		top = UD[i]-DD[i]
		bottom = UD[i]+DD[i]
		if bottom != 0:
			CMO.append(top/bottom)
		else:
			# TODO CHANGE THIS IF NEEDED
			CMO.append(1)

	k = [abs(x) for x in CMO]

	# print(CMO[-5:])
	# print(k[-5:])
	"""
	Var=0.0
	Var:=(alpha*k*src)+(1-alpha*k)*nz(Var[1])
	"""

	Var = [0.0]

	for i in range(1, len(src)):
		# print(i)
		# print(k[i])
		# print(src[i])
		# print(Var[i-1])
		Var.append(alpha*k[i]*src[i] + (1-alpha*k[i])*nz(Var[i-1]))

	# print(Var[-5:])

	"""
	fark=Var*percent*0.01
	longStop = Var - fark
	longStopPrev = nz(longStop[1], longStop)
	longStop := Var > longStopPrev ? max(longStop, longStopPrev) : longStop
	"""
	fark = [Var[i]*percent*0.01 for i in range(len(Var))]
	longStop = [Var[i] - fark[i] for i in range(len(Var))]
	longStopPrev = [longStop[0]]
	for i in range(1, len(longStop)):
		if longStop[i-1] != None:
			longStopPrev.append(longStop[i-1])
		else:
			longStopPrev.append(longStop[i])
	
	newLongStop = [max(longStop[i], longStopPrev[i]) \
		if Var[i] > longStopPrev[i] else longStop[i] for i in range(len(Var))]
	
	longStop = newLongStop

	""" 
	shortStop =  Var + fark
	shortStopPrev = nz(shortStop[1], shortStop)
	shortStop := Var < shortStopPrev ? min(shortStop, shortStopPrev) : shortStop
	"""
	shortStop = [Var[i] + fark[i] for i in range(len(Var))]

	shortStopPrev = [shortStop[0]]
	for i in range(1, len(shortStop)):
		shortStopPrev.append(nz(shortStop[i-1], shortStop[i]))

	newShortStop = [min(shortStop[i], shortStopPrev[i]) \
		if Var[i] < shortStopPrev[i] else shortStop[i] for i in range(len(Var))]
	
	shortStop = newShortStop

	# print(longStop[-3:])
	# print(shortStop[-3:])

	"""
	dir = 1
	dir := nz(dir[1], dir)
	"""
	dir_ = [1]
	for i in range(1, len(src)):
		try:
			dir_.append(dir_[i-1])
		except IndexError:
			dir_.append(dir_[i])

	# dir := dir == -1 and Var > shortStopPrev ? 1 : dir == 1 and Var < longStopPrev ? -1 : dir
	for i in range(0, len(longStopPrev)):
		if dir_[i] == -1 and Var[i] > shortStopPrev[i]:
			dir_[i] = 1
		elif dir_[i] == 1 and Var[i] < longStopPrev[i]:
			dir_[i] = -1
	
	# print(dir_[-5:])

	"""
	MT = dir==1 ? longStop: shortStop
	OTT=Var>MT ? MT*(200+percent)/200 : MT*(200-percent)/200 
	"""
	MT = [longStop[i] if dir_[i]==1 else shortStop[i] for i in range(len(dir_))]
	OTT = [MT[i]*(200+percent)/200 if Var[i]>MT[i] else MT[i]*(200-percent)/200 for i in range(len(MT))]
	
	# print(MT[-5:])
	# print(OTT[-5:])

	return Var, OTT

def sma(df, source, period):
  return pyti_sma(df[source].tolist(), period)

def ema(df, source, period):
  return pyti_ema(df[source].tolist(), period)

def lbb(df, source, period):
  return pyti_lbb(df[source].tolist(), period)

def ubb(df, source, period):
  return pyti_ubb(df[source].tolist(), period)

def rsi(df, source, period):
  return pyti_rsi(df[source].tolist(), period)

def HA(df, ohlc=['open', 'high', 'low', 'close']):
	"""
	Function to compute Heiken Ashi Candles (HA)
	
	Args 
	--
	df : Pandas DataFrame which contains `['date', 'open', 'high', 'low', 'close', 'volume']` columns
	ohlc: List defining OHLC Column names (default `['open', 'high', 'low', 'close']`)
			
	Returns 
	--
	df : Pandas DataFrame with new columns added for 
			Heiken Ashi Close (HA_$ohlc[3])
			Heiken Ashi Open (HA_$ohlc[0])
			Heiken Ashi High (HA_$ohlc[1])
			Heiken Ashi Low (HA_$ohlc[2])
	"""

	ha_open = 'HA_' + ohlc[0]
	ha_high = 'HA_' + ohlc[1]
	ha_low = 'HA_' + ohlc[2]
	ha_close = 'HA_' + ohlc[3]
	
	df[ha_close] = (df[ohlc[0]] + df[ohlc[1]] + df[ohlc[2]] + df[ohlc[3]]) / 4

	df[ha_open] = 0.00
	for i in range(0, len(df)):
			if i == 0:
					df[ha_open].iat[i] = (df[ohlc[0]].iat[i] + df[ohlc[3]].iat[i]) / 2
			else:
					df[ha_open].iat[i] = (df[ha_open].iat[i - 1] + df[ha_close].iat[i - 1]) / 2
					
	df[ha_high]=df[[ha_open, ha_close, ohlc[1]]].max(axis=1)
	df[ha_low]=df[[ha_open, ha_close, ohlc[2]]].min(axis=1)

	return df

def isSupport(df,i):
	return df['low'][i] < df['low'][i-1] \
		and df['low'][i] < df['low'][i+1] \
		and df['low'][i+1] < df['low'][i+2] \
		and df['low'][i-1] < df['low'][i-2] 

def isResistance(df,i):
	return df['high'][i] > df['high'][i-1] \
		and df['high'][i] > df['high'][i+1] \
		and df['high'][i+1] > df['high'][i+2] \
		and df['high'][i-1] > df['high'][i-2] 


INDICATOR_DICT = {
	"sma": sma,
	"ema": ema,
	"lbb": lbb,
	"ubb": ubb,
	"cci": cci,
	"rsi": rsi,
	"smoothrng": smoothrng,
	"ott": ott
}

def AddIndicator(df, indicator_name:str, col_name, *args):
	try:
		if indicator_name == "ott":
			df[col_name[0]], df[col_name[1]] = ott(df, *args)
		else:
			df[col_name] = INDICATOR_DICT[indicator_name](df, *args)
	except Exception as e:
		print_exc()
		print("\nException raised when trying to compute the", indicator_name, "indicator:\n")
	