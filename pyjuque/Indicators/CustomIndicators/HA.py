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