import numpy as np
import pandas as pd

def ST(data, period, factor, ohlc=['open', 'high', 'low', 'close']): 
		# df is the dataframe, n is the period, f is the factor; f=3, n=7 are commonly used.
		n = period

		df = data.copy()
		c_open = ohlc[0]
		c_high = ohlc[1]
		c_low = ohlc[2]
		c_close = ohlc[3]
		
		# ATR Calculation
		df['h-l'] = abs(df[c_high] - df[c_low])
		df['h-pc'] = abs(df[c_high] - df[c_close].shift(1))
		df['l-pc'] = abs(df[c_low] - df[c_close].shift(1))
		df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
		df['atr'] = np.nan 
		df.loc[n-1, 'atr'] = df['tr'][:n-1].mean()
		for i in range(n, len(df)):
				df['atr'][i] = (df['atr'][i-1] * (n-1) + df['tr'][i])/n

		hl2 = (df[c_high] + df[c_low])/2
		df['upper_basic'] = hl2 + factor * df['atr']
		df['lower_basic'] = hl2 - factor * df['atr']
		df['upper_band'] = df['upper_basic']
		df['lower_band'] = df['lower_basic']

		for i in range(n, len(df)):
				if df[c_close][i-1] <= df['upper_band'][i-1]:
						df['upper_band'][i] = min(df['upper_basic'][i], df['upper_band'][i-1])
				else:
						df['upper_band'][i] = df['upper_basic'][i]
		
		for i in range(n,len(df)):
				if df[c_close][i-1]>=df['lower_band'][i-1]:
						df['lower_band'][i] = max(df['lower_basic'][i], df['lower_band'][i-1])
				else:
						df['lower_band'][i] = df['lower_basic'][i] 

		df['supertrend'] = np.nan

		for i in df['supertrend']:
				if df[c_close][n-1]<=df['upper_band'][n-1]:
						df['supertrend'][n-1]=df['upper_band'][n-1]
				elif df[c_close][n-1]>df['upper_band'][i]:
						df['supertrend'][n-1]=df['lower_band'][n-1]
		for i in range(n,len(df)):
				if df['supertrend'][i-1]==df['upper_band'][i-1] and df[c_close][i]<=df['upper_band'][i]:
						df['supertrend'][i]=df['upper_band'][i]
				elif  df['supertrend'][i-1]==df['upper_band'][i-1] and df[c_close][i]>=df['upper_band'][i]:
						df['supertrend'][i]=df['lower_band'][i]
				elif df['supertrend'][i-1]==df['lower_band'][i-1] and df[c_close][i]>=df['lower_band'][i]:
						df['supertrend'][i]=df['lower_band'][i]
				elif df['supertrend'][i-1]==df['lower_band'][i-1] and df[c_close][i]<=df['lower_band'][i]:
						df['supertrend'][i]=df['upper_band'][i]

		return df
