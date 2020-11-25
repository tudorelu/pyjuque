import pandas as pd
from pyjuque.Indicators import AddIndicator
from abc import ABC, abstractmethod
from pprint import pprint

class Strategy(ABC):
    def __init__(self):
        self.df = None
        self.indicators = None

    def setUp(self, df):
        self.df = df
        if self.indicators is not None:
            # Create all asked indicators
            for indicator in self.indicators:
                exclude_keys = set(['indicator_name', 'col_name', 'indicator_function'])
                args = [indicator[k] 
                    for k in indicator.keys() if k not in exclude_keys]
                
                # print("For {} we have args {}".format(indicator["indicator_name"], args))

                if 'indicator_function' in indicator.keys():
                    col_name = indicator['col_name']
                    indicator_function = indicator['indicator_function']
                    ret = indicator_function(self.df, *args)
                    
                    cols_dict = dict()
                    i = 0
                    for cname in col_name:
                        cols_dict[cname] = ret[i]
                        i += 1

                    self.df = self.df.assign(**cols_dict) 

                else:
                    # Create a list of all arguments that are not the 
                    # indicator name or column name
                    AddIndicator(
                        self.df, indicator['indicator_name'], 
                        indicator['col_name'], *args)
        return self.df

    @abstractmethod
    def chooseIndicators(self):
        """ Checks whether we have a long signal """
        pass

    @abstractmethod
    def checkLongSignal(self, i):
        """ Checks whether we have a long signal """
        pass

    @abstractmethod
    def checkShortSignal(self, i):
        """ Checks whether we have a short signal """
        pass

    def checkToExitLongPosition(self, i):
        """ Checks whether we should exit a long position
        (Most times this is equivalent to checkShortSignal) """
        return self.checkShortSignal(i)

    def checkToExitShortPosition(self, i):
        """ Checks whether we should exit a short position
        (Most times this is equivalent to checkLongSignal) """
        return self.checkLongSignal(i)
