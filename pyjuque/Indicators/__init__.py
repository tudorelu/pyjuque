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

from pyjuque.Indicators.CustomIndicators.SuperTrend import ST
from pyjuque.Indicators.CustomIndicators.OTT import ott, smoothrng
from pyjuque.Indicators.CustomIndicators.HA import HA
from traceback import print_exc

def cci(df, period):
    return commodity_channel_index(
        df['close'].tolist(), df['high'].tolist(), df['low'].tolist(), period)

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
    # print("Args are", indicator_name, col_name)
    # print(args)
    try:
        if indicator_name == "ott":
            df[col_name[0]], df[col_name[1]] = ott(df, *args)
        else:
            df[col_name] = INDICATOR_DICT[indicator_name](df, *args)
    except Exception as e:
        print_exc()
        print("\nException raised when trying to compute the", indicator_name, "indicator:\n")
    