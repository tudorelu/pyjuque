
# Imports for the strategy
import pandas_ta as ta

# Importing these to be able to run this example 
# from the main pyjuque folder
from os import getenv
from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)

# Import for defining the Strategy
from pyjuque.Strategies import StrategyTemplate
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from pyjuque.Engine.BacktesterSundayTheQuant import Backtester
from pyjuque.Plotting import PlotData
from pprint import pprint
import time

## Defines the strategy
class EMACross(StrategyTemplate):
    """ Bollinger Bands x RSI """
    minimum_period = 100
    def __init__(self, fast_ma_len = 10, slow_ma_len = 50):
        self.fast_ma_len = fast_ma_len
        self.slow_ma_len = slow_ma_len
        # the minimum number of candles needed to compute our indicators
        self.minimum_period = max(100, slow_ma_len)


    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df):
        df['slow_ma'] = ta.ema(df['close'], self.slow_ma_len)
        df['fast_ma'] = ta.ema(df['close'], self.fast_ma_len)
        self.dataframe = df


    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place a long order
    def checkLongSignal(self, i = None):
        """ """
        df = self.dataframe
        if i == None:
            i = len(df) - 1
        if i < 1:
            return False
        if df['low'][i-1] < df['slow_ma'][i-1] and df['low'][i] > df['slow_ma'][i] \
            and df['low'][i] > df['fast_ma'][i] and df['fast_ma'][i] > df['slow_ma'][i]:
            return True
        return False

    # if your exit settings contain 'exit on signa;', the bot will exit if it has an open
    # order and it receives a short signal (if this function returns true)
    def checkShortSignal(self, i = None):
        df = self.dataframe
        if i == None:
            i = len(df) - 1
        if i < 1:
            return False
        if (df['low'][i-1] > df['slow_ma'][i-1] or df['fast_ma'][i-1] > df['slow_ma'][i-1] ) \
            and df['close'][i] < df['slow_ma'][i] and df['close'][i] < df['fast_ma'][i] \
            and df['fast_ma'][i] < df['slow_ma'][i]:
            return True
        return False


bot_config = {
    'name' : 'my_kucoin_bot_testing',
    'test_run' : True,
    'exchange' : {
        'name' : 'kucoin',
        'params' : {
            # 'api_key': getenv('KUCOIN_API_KEY'),
            # 'secret' : getenv('KUCOIN_API_SECRET'),
            # 'password' : getenv('KUCOIN_PASSWORD'),
        },
    },
    'symbols' : ['SNX/USDT', 'XLM/USDT'], # the backtester will ignore this for now
    'starting_balance' : 100,
    'strategy': {
        'class': EMACross,
        'params': {
            'fast_ma_len' : 8, 
            'slow_ma_len' : 30, 
        }
    },
    'timeframe' : '1m',
    'entry_settings' : {
        'initial_entry_allocation': 10,
        'signal_distance': 0.3,
        'leverage': 1,
    },
    'exit_settings' : {
        'take_profit' : 10,
        'stop_loss_value': 20,
        'exit_on_signal': True
    }
}

def Main():
    # backtests a bot using the same config that can run a bot
    
    # For the backtester, we initialise the exchange 
    exchange = CcxtExchange('kucoin')
    # and download the data
    df = exchange.getOHLCV('BTC/USDT', '1m', 1000)

    # we then initialize the backtester using the config dict
    bt = Backtester(bot_config)
    # and run it on the data downloaded before
    bt.backtest(df)

    # we then retreive and print the results
    results = bt.return_results()
    pprint(results)
    
    # and we also Plot OHLCV, indicators & signals
    PlotData(df, 
        plot_indicators=[
            dict(name = 'slow_ma', title = 'SLOW HMA'),
            dict(name = 'fast_ma', title = 'FAST HMA'),
        ],
        signals=[
            dict(name = 'entry orders', points = bt.entries), 
            dict(name = 'exit orders', points = bt.exits),
        ], show_plot=True)


if __name__ == '__main__':
    Main()
