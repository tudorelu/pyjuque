import os 
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.insert(1, root_path)

from pyjuque.Engine import Models 

from pyjuque.Plotting import PlotData
from tests.utils import get_session
import unittest
from unittest.mock import patch
import pandas

class TestSqliteDecimal(unittest.TestCase):
    
    def setUp(self):
        self.df_adabtc_1k = pandas.read_csv('tests/data/ADABTC_1m_1k.csv')
        self.df_btcusd_1k = pandas.read_csv('tests/data/BTCUSD_1m_1k.csv')
        self.df_btcusd_10k = pandas.read_csv('tests/data/BTCUSD_1m_10k.csv')
        
    def test_entry_exit_signal(self):
        """ test initialization for sqlitedecimal class """
        pass
        dfs = dict(
            ADABTC = self.df_adabtc_1k,
            BTCUSD = self.df_btcusd_1k)

        def entryFunction(bot_controller, symbol):
            df = dfs[symbol]
            df['sma_50'] = df.iloc[:,1].rolling(window=50).mean()
            df['sma_140'] = df.iloc[:,1].rolling(window=140).mean()
            if df['sma_50'].iloc(-1) > df['sma_140'].iloc(-1) and \
                df['sma_50'].iloc(-2) < df['sma_140'].iloc(-2):
                return True, df['close'].iloc(-1)
            return False, df['close'].iloc(-1)
        
        def exitFunction(bot_controller, symbol):
            df = dfs[symbol]
            df['sma_50'] = df.iloc[:,1].rolling(window=50).mean()
            df['sma_140'] = df.iloc[:,1].rolling(window=140).mean()
            if df['sma_50'].iloc(-1) < df['sma_140'].iloc(-1) and \
                df['sma_50'].iloc(-2) > df['sma_140'].iloc(-2):
                return True, df['close'].iloc(-1)
            return False, df['close'].iloc(-1)
        
        bot_config = {
            'name' : 'my_custom_test_bot',
            'exchange' : {
                'name' : 'kucoin',
                'params' : {},
            },
            'timeframe' : '1m',
            'test_run': True,
            'symbols' : ['ADA/BTC', 'BTC/USD'],
            'starting_balance' : 10000,
            'strategy': {
                'custom': True,
                'entry_function': entryFunction,
                'exit_function': exitFunction,
            },
            'entry_settings' : {
                'initial_entry_allocation': 1,
                'signal_distance': 0.2
            },
            'exit_settings' : {
                'exit_on_signal' : True,
            }
        }

        bot_controller = defineBot(bot_config)
        for i in range(200, 1000):
            bot_controller.executeBot()


if __name__ == '__main__':
    unittest.main()