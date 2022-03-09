from pyjuque.Strategies import Strategy
from pandas import DataFrame

## Defines the strategy
class MomentumStrategy(Strategy):
    minimum_period = 100
    def __init__(self, momentum_period=3):
        if momentum_period < 1:
            raise ValueError("momentum_period should be greater than 1.")
        self.momentum_period = momentum_period
        self.minimum_period = max(100, momentum_period)


    def set_up(self, candles:DataFrame):
        """
        The bot will call this function with the latest data.
        It computes two arrays, one for long and one for short 
        signals which should be of the same length as the data
        """
        long_signals = [0] * self.momentum_period
        short_signals = [0] * self.momentum_period
        l_df = len(candles)
        close = candles['close']
        for i in range(self.momentum_period, l_df):
            all_increasing = True
            all_decreasing = True
            # Go through the last 'momentum_period' candles 
            # to see if they're all increasing, decreasing, or nothing.
            for j in range(i + 1 - self.momentum_period, i + 1):
                all_increasing = all_increasing and (close[j] > close[j-1])
                all_decreasing = all_decreasing and (close[j] < close[j-1])
            long_signals.append(int(all_increasing))
            short_signals.append(int(all_decreasing))
        self.long_signals = long_signals
        self.short_signals = short_signals
        self.candles = candles


    def check_long_signal(self, i = None):
        """
        The bot will call this function with the latest data and if this 
        returns true, our bot will place a long order
        """
        return self.long_signals[i], None
    

    def check_short_signal(self, i = None):
        """
        If your bot / backtester config contains 'exit on signal', it 
        will exit if it has an open order and it receives a short signal
        """
        return self.short_signals[i], None

