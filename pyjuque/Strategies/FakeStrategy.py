import numpy as np
from pyjuque.Strategies import Strategy


class FakeStrategy(Strategy):
    def __init__(self, long_signals:np.ndarray=None, short_signals:np.ndarray=None):
        super().__init__()
        if long_signals is None and short_signals is None:
            raise NotImplementedError("You must provide long_signals and/or short_signals")
        elif long_signals is None:
            self.long_signals = np.zeros(len(short_signals))
            self.short_signals = short_signals
        elif short_signals is None:
            self.short_signals = np.zeros(len(long_signals))
            self.long_signals = long_signals
        else:
            self.long_signals = long_signals
            self.short_signals = short_signals


    def set_up(self, candles):
        self.candles = candles


    def check_long_signal(self, candle_index: int) -> bool:
        return self.long_signals[candle_index] == 1


    def check_short_signal(self, candle_index: int) -> bool:
        return self.short_signals[candle_index] == 1

