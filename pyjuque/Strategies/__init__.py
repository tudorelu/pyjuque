from abc import ABC, abstractmethod

class StrategyTemplate(ABC):

    minimum_period = 100
    indicators = []
    df = None

    @abstractmethod
    def setUp(self, df):
        """ Computes the indicators for the given dataframe 
        (usually gets called by the bot controller when recent candlestick 
        data is received from the exchange)"""
        pass


    @abstractmethod
    def checkLongSignal(self, i):
        """ Checks whether we have a long signal """
        pass


    @abstractmethod
    def checkShortSignal(self, i):
        """ Checks whether we have a short signal """
        pass
