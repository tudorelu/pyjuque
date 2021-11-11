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
from pyjuque.Backtester import Backtester
from pprint import pprint
from time import time as timer

## Defines the strategy
class MomentumStrategy(StrategyTemplate):
    """ Bollinger Bands x RSI """
    minimum_period = 100
    def __init__(self, momentum_period=3):
        if momentum_period < 1:
            raise ValueError("momentum_period should be greater than 1.")
        self.momentum_period = momentum_period
        self.minimum_period = max(100, momentum_period)

    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df):
        long_signals = [0] * self.momentum_period
        short_signals = [0] * self.momentum_period
        l_df = len(df)
        close = df['close']
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
        self.dataframe = df
    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place a long order
    def checkLongSignal(self, i = None):
        return self.long_signals[i], None
    # if your exit settings contain 'exit on signa;', the bot will exit if it has an open
    # order and it receives a short signal (if this function returns true)
    def checkShortSignal(self, i = None):
        return self.short_signals[i], None

bot_config = {
    'strategy': {
        'class': MomentumStrategy,
        'params': {'momentum_period' : 2}
    },
    'entry_settings' : {
        'trade_amount': 1_000,
        'go_long' : True,
        'go_short' : False,
        'fee': 0.1
    },
    'exit_settings' : {
        'exit_on_signal': True
    }
}

if __name__ == '__main__':
    # Get data from exchange
    symbol= "BTC/USDT"
    exchange = CcxtExchange('binance', {'enableRateLimit':True})
    df = exchange.getOHLCVHistorical(symbol, '1h', 1000)
    # Backtest bot on this data
    bt = Backtester(bot_config)
    bt.backtest(df)
    bt.get_fig().show()
