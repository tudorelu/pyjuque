import time

# Import for defining the bot
from pyjuque.Bot import defineBot

# Imports for the strategy
import pandas_ta as ta
from pyjuque.Strategies import StrategyTemplate

# Importing these to be able to run this example 
# from the main pyjuque folder
from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)


def customEntryStrategy(bot_controller, symbol):
    ## This is the function that pyjuque will call to check for entry signal
    ## the first parammeter is a bot_controller, through which we have access 
    ## to the following objects:
    ##
    ## bot_controller.bot_model (a SQLAlchemy model, containing the info that 
    #       we store in the database for this bot plus a few methods)
    ## bot_controller.session (a SQLAlchemy database session)
    ## bot_controller.exchange (a CcxtExchanges, exposing a few wrapped methods 
    ##      written to work with pyjuque plus all the ccxt unified api methods, 
    ##      through bot_controller.exchange.ccxt)
    ## bot_controller.strategy (in our case it will be None)
    ## bot_controller.status_printer (yaspin object)
    ##
    ## and the following method:
    ## bot_controller.executeBot() (executes a loop of the bot - checking
    ##      entry signals on all symbols, placing orders if any signals are 
    ##      found, then checking all the open orders and updating them)
    ##
    ## it returns a boolean (the signal) and the current price of the asset
    
    # Get data from exchange for multiple timeframes
    df_15min = bot_controller.exchange.getOHLCV(symbol, '15m', limit=100)
    df_1hour = bot_controller.exchange.getOHLCV(symbol, '1h', limit=100)
    df_4hour = bot_controller.exchange.getOHLCV(symbol, '4h', limit=100)

    # Define and compute indicators for each timeframe
    Strat = ta.Strategy(
        name="EMAs",
        ta=[
            {"kind": "ema", "length": 20},
            {"kind": "ema", "length": 50},
        ]
    )
    df_15min.ta.strategy(Strat)
    df_1hour.ta.strategy(Strat)
    df_4hour.ta.strategy(Strat)
    
    # Check entry signal on each timeframe separately
    entry_signal_15 = df_15min.iloc[-1]['EMA_50'] > df_15min.iloc[-1]['EMA_20']
    entry_signal_1h = df_1hour.iloc[-1]['EMA_50'] > df_1hour.iloc[-1]['EMA_20']
    entry_signal_4h = df_4hour.iloc[-1]['EMA_50'] > df_1hour.iloc[-1]['EMA_20']

    # Combine them
    entry_signal = entry_signal_15 and entry_signal_1h and entry_signal_4h
    
    # Return the signal and the last price
    return entry_signal, df_4hour.iloc[-1]['close']


## Defines the overall configuration of the bot 
bot_config = {
    # Name of the bot, as stored in the database
    'name' : 'my_bot',

    # URL of the database which stores this bot
    'db_url' : 'sqlite:///my_simple_bot.db',

    # bot type, 'ta' for technical analysis or 'grid'
    'type' : 'ta',

    # time in seconds it waits between checking price & orders
    'sleep': 40,

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

    # quote asset of starting balance
    'quote_asset': 'BTC',

    # strategy class / function (here we define the entry and exit strategies.)
    # this bot places an entry order when 'customEntryStrategy' retruns true
    'strategy': {
        'custom': True,
        'entry_function': customEntryStrategy,
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

    # will the bot use a logger to log/print important actions 
    # (like placing orders) in the terminal
    'use_logger' : True,

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
        # waits bot_config['sleep'] seconds between rounds
        time.sleep(bot_config['sleep'])


if __name__ == '__main__':
    Main()
