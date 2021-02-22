import time

# Imports for the strategy
import pandas_ta as ta

# Importing these to be able to run this example 
# from the main pyjuque folder
from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)

# Import for defining the bot
from pyjuque.Bot import defineBot
# Import for defining the Strategy
from pyjuque.Strategies import StrategyTemplate

## Defines the strategy
class BBRSIStrategy(StrategyTemplate):
    """ Bollinger Bands x RSI """
    def __init__(self, rsi_len = 8, bb_len = 100, rsi_ob = 50, rsi_os = 50):
        self.rsi_ob = rsi_ob
        self.rsi_os = rsi_os
        self.bb_len = bb_len
        self.rsi_len = rsi_len

        # the minimum number of candles needed to compute our indicators
        self.minimum_period = max(100, bb_len, rsi_len)

    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df):
        df['rsi'] = ta.rsi(df['close'], self.rsi_len)
        df['lbb'], df['mbb'], df['ubb'], df['bb_width'] = ta.bbands(df['close'], self.bb_len)
        self.dataframe = df

    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place an order
    def checkLongSignal(self, i = None):
        """ if the rsi had a sudden increase this candle or the previous one, 
        and one of the previous three values of the rsi was under the oversold 
        level, and the price just crossed over the lower bollinger band, buy"""
        df = self.dataframe
        if i == None:
            i = len(df) - 1
        if i < 3:
            return False
        if (df["rsi"][i] / df["rsi"][i-1] > 1.2) and \
            (df["rsi"][i-1] < self.rsi_os \
                or df["rsi"][i-2] < self.rsi_os \
                or df["rsi"][i-3] < self.rsi_os):
            if ((df["open"][i] < df["lbb"][i] < df["close"][i]) and \
                (df["open"][i-1] < df["lbb"][i-1] and df["close"][i-1] < df["lbb"][i-1])):
                return True
        if (df["rsi"][i-1] / df["rsi"][i-2] > 1.2) and \
            (df["rsi"][i-1] < self.rsi_os \
                or df["rsi"][i-2] < self.rsi_os \
                or df["rsi"][i-3] < self.rsi_os):
            if (df["close"][i-3] < df["lbb"][i-3] and df["close"][i-2] < df["lbb"][i-2] \
                and df["close"][i-1] > df["lbb"][i-1] and df["close"][i] > df["lbb"][i]):
                return True
        return False

    # we don't exit on signal, only on take profit pr stop loss level reached
    def checkShortSignal(self, i = None):
        return False


## Defines the overall configuration of the bot 
bot_config = {
    # Name of the bot, as stored in the database
    'name' : 'my_bot',
    
    # exchange information (fill with your api key and secret)
    'exchange' : {
        'name' : 'binance',
        'params' : {
            'api_key': '...',
            'secret' : '...'
        },
    },

    # symbols to trade on
    'symbols' : ['LINK/BTC', 'ETH/BTC'],

    # starting balance for bot
    'starting_balance' : 0.0005,

    # strategy class / function (here we define the entry and exit strategies.)
    # this bot places an entry order when the 'checkLongSignal' function of 
    # the strategy below retruns true
    'strategy': {
        'class': BBRSIStrategy,
        'params': {
            'rsi_len' : 8, 
            'bb_len' : 100, 
            'rsi_ob' : 50, 
            'rsi_os' : 50
        }
    },

    # when the bot receives the buy signal, the order is placed according 
    # to the settings specified below
    'entry_settings' : {

        # between 0 and 100, the % of the starting_balance to put in an order
        'initial_entry_allocation': 100,

        # number between 0 and 100 - 1% means that when we get a buy signal, 
        # we place buy order 1% below current price. if 0, we place a market 
        # order immediately upon receiving signal
        'signal_distance': 0.3
    },

    # This bot exits when our filled orders have reached a take_profit % above 
    # the buy price, or a stop_loss_value % below it
    'exit_settings' : {

        # take profit value between 0 and infinity, 3% means we place our sell 
        # orders 3% above the prices that our buy orders filled at
        'take_profit' : 3,

        # stop loss value in percent - 10% means stop loss at 10% below our 
        # buy order's filled price
        'stop_loss_value': 10
    },

    # will the bot display its status / current performing action in the terminal
    'display_status' : True
}


## Runs the bot in an infinite loop, stoppable from the terminal with CTRL + C
def Main():
    bot_controller = defineBot(bot_config)
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        
        time.sleep(60)


if __name__ == '__main__':
    Main()
