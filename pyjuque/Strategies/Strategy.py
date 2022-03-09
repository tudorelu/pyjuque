from abc import ABC, abstractmethod
from pandas import DataFrame
from numpy import where
from pyjuque.Plotter import GraphDetails

class Strategy(ABC):
    """
    Abstract class for strategies.
    """

    def __init__(self):
        self.long_signals = None
        self.short_signals = None
        self.exit_long_signals = None
        self.exit_short_signals = None
        self.candles = None


    @abstractmethod
    def set_up(self, candles:DataFrame, *args:list, **kwargs:dict):
        """
        Computes the long and the short signals.
        """


    @abstractmethod
    def check_long_signal(self, candle_index:int) -> bool:
        """
        Returns True if the strategy wants to go long on candle 
        numbered `candle_index`.
        """


    @abstractmethod
    def check_short_signal(self, candle_index:int) -> bool:
        """
        Returns True if the strategy wants to go short on candle 
        numbered `candle_index`.
        """


    def get_plottable_indicators(self) -> list:
        """
        Returns a list of GraphDetails objects, one for each indicator 
        that can be used to plot the signals.
        """
        return []


    def get_plottable_signals(self, **kwargs) -> list:
        """
        Returns a list of GraphDetails objects, one for each signal 
        type that can be used to plot the signals.
        """
        long_candles = self.candles.iloc[where(self.long_signals == 1)[0]]
        short_candles = self.candles.iloc[where(self.short_signals == 1)[0]]
        exit_long_candles = self.candles.iloc[where(self.exit_long_signals == 1)[0]]
        exit_short_candles = self.candles.iloc[where(self.exit_short_signals == 1)[0]]
        longs_graph = GraphDetails(
            name='Long Signals', 
            color='green', 
            mode='markers', 
            marker_symbol='triangle-up',
            xsource=long_candles.time.values, 
            ysource=long_candles.close.values * 0.9997,
            **kwargs)
        exit_longs_graph = GraphDetails(
            name='Exit Long Signals', 
            color='red', 
            mode='markers', 
            marker_symbol='arrow-bar-left',
            xsource=exit_long_candles.time.values, 
            ysource=exit_long_candles.close.values * 0.9997,
            **kwargs)
        shorts_graph = GraphDetails(
            name='Short Signals', 
            color='red', 
            mode='markers', 
            marker_symbol='triangle-down',
            xsource=short_candles.time.values, 
            ysource=short_candles.close.values * 1.0003,
            **kwargs)
        exit_shorts_graph = GraphDetails(
            name='Exit Short Signals', 
            color='green', 
            mode='markers', 
            marker_symbol='arrow-bar-left',
            xsource=exit_short_candles.time.values, 
            ysource=exit_short_candles.close.values * 0.9997,
            **kwargs)
        return [longs_graph, exit_longs_graph, shorts_graph, exit_shorts_graph]

