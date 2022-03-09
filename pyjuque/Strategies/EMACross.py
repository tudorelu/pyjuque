
from pyjuque.Plotter.Utils import GraphDetails
from .Strategy import Strategy

import pandas_ta as ta
import numpy as np

## Defines the strategy
class EMACrossStrategy(Strategy):
    minimum_period = 100
    def __init__(self, fast_ma_len = 10, slow_ma_len = 50):
        self.fast_ma_len = fast_ma_len
        self.slow_ma_len = slow_ma_len
        # the minimum number of candles needed to compute our indicators
        self.minimum_period = max(100, slow_ma_len)

    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def set_up(self, df):
        df['slow_ma'] = ta.ema(df['close'], self.slow_ma_len)
        df['fast_ma'] = ta.ema(df['close'], self.fast_ma_len)
        prev_slow_ma = df['slow_ma'].shift(1)
        prev_fast_ma = df['fast_ma'].shift(1)
        self.long_signals = np.where(prev_slow_ma > prev_fast_ma, 
            np.where(df['slow_ma'] < df['fast_ma'], 1, 0), 0)
        self.short_signals = np.where(prev_slow_ma < prev_fast_ma, 
            np.where(df['slow_ma'] > df['fast_ma'], 1, 0), 0)
        self.candles = df

    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place a long order
    def check_long_signal(self, i = None):
        return self.long_signals[i] == 1, None

    # if your exit settings contain 'exit on signa;', the bot will exit if it has an open
    # order and it receives a short signal (if this function returns true)
    def check_short_signal(self, i = None):
        return self.short_signals[i] == 1, None

    def get_plottable_indicators(self) -> list:
        return [
            GraphDetails(name='slow_ma'),
            GraphDetails(name='fast_ma')
        ]
