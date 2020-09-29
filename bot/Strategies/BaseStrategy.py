from bot.Indicators import AddIndicator # pylint: disable=E0401
from abc import ABC, abstractmethod


class Strategy(ABC):
    def __init__(self):
        self.df = None
        self.indicators = None
    
    def setUp(self):
        self.current_price = self.df.iloc[-1]['close']
        self.chooseIndicators()
        if self.indicators is not None:
            # Create all asked indicators
            for indicator in self.indicators:
                # Create a list of all arguments that are not the indicator name or column name
                exclude_keys = set(['indicator_name', 'col_name'])
                args = [indicator[k] for k in set(list(indicator.keys())) - exclude_keys]
                
                AddIndicator(self.df, indicator['indicator_name'], indicator['col_name'], *args)
    
    def shouldEntryOrder(self, df):
        self.df = df
        self.setUp()
        i = len(self.df) - 1
        long_signal = self.checkLongSignal(i)
        short_signal = self.checkShortSignal(i)

        if long_signal and short_signal:
            raise Exception('Cannot enter long and short signal at the same time')
        if long_signal:
            return long_signal
        if short_signal:
            raise Exception('Short positions not supported yet.')
        return False
        
    def shouldExitOrder(self, df):
        self.df = df
        self.setUp()
        i = len(self.df) - 1
        exit_signal = self.checkToExitPosition(i)
        return exit_signal
            
    @abstractmethod
    def checkLongSignal(self, i):
        pass
    
    @abstractmethod
    def checkShortSignal(self, i):
        pass

    @abstractmethod
    def checkToExitPosition(self, i):
        pass

    @abstractmethod
    def chooseIndicators(self):
        pass
