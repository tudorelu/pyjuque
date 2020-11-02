# TI & TA
from pyti.smoothed_moving_average import smoothed_moving_average as sma
from pyti.bollinger_bands import lower_bollinger_band as lbb
from pyti.bollinger_bands import upper_bollinger_band as ubb
from pyti.accumulation_distribution import accumulation_distribution as acd
from pyti.aroon import aroon_up
from pyti.aroon import aroon_down

from pyti.rate_of_change import rate_of_change as roc
from pyti.relative_strength_index import relative_strength_index as rsi
from pyti.commodity_channel_index import commodity_channel_index 
from pyti.exponential_moving_average import exponential_moving_average as ema

from traceback import print_exc

def cci(df, period):
	return commodity_channel_index(df['close'].tolist(), df['high'].tolist(), df['low'].tolist(), period)

INDICATOR_DICT = {
	"sma": sma,
	"ema": ema,
	"lbb": lbb,
	"ubb": ubb,
	"cci": cci,
	"roc": roc,
	"rsi": rsi,
}

def AddIndicator(df, indicator_name:str, col_name:str=None, *args):
	try:
		if indicator_name == "cci":
			df[col_name] = cci(df, *args)
		else:
			df[col_name] = INDICATOR_DICT[indicator_name](df['close'].tolist(), *args)
	except Exception as e:
		print_exc()
		print("\nException raised when trying to compute the", indicator_name, "indicator:\n")
	