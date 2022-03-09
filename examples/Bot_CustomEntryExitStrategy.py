import time

# Imports for the strategy
import pandas_ta as ta

# Import for defining the bot
from pyjuque.Bot import defineBot
# Import for Plotting
from pyjuque.Plotter import create_plot as PlotData
import plotly.graph_objs as go


def plot(df, plot_title):
    PlotData(df, plot_indicators=[
        dict(name = 'HMA_20', title = 'HMA'),
    ], show_plot=True, plot_title=plot_title)


# Entry Strategy Function
def customEntryStrategy(bot_controller, symbol):
    """ Entry on price crossover HMA """ 
    try:
        df = bot_controller.exchange.getOHLCV(symbol, '1m', limit=400)
        df.ta.hma(length=20, append=True)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        print(' Could not get data or compute indicator on {}'.format(symbol))
        return False, None
    
    prev_price = df['close'].iloc[-2]
    prev_hma = df['HMA_20'].iloc[-2]

    current_price = df['close'].iloc[-1]
    current_hma = df['HMA_20'].iloc[-1]

    if current_price > current_hma and prev_price < prev_hma:
        plot(df, 'entry_signal_{}'.format(symbol.replace('/', '_')))
        return True, current_price 

    return False, current_price



def customExitStrategy(bot_controller, symbol):
    """ Exit on price crossunder HMA """ 
    try:
        df = bot_controller.exchange.getOHLCV(symbol, '1m', limit=400)
        df.ta.hma(length=20, append=True)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        print(' Could not get data or compute indicator on {}'.format(symbol))
        return False, None
    
    prev_price = df['close'].iloc[-2]
    prev_hma = df['HMA_20'].iloc[-2]

    current_price = df['close'].iloc[-1]
    current_hma = df['HMA_20'].iloc[-1]

    if current_price < current_hma and prev_price > prev_hma:
        plot(df, 'exit_signal_{}'.format(symbol.replace('/', '_')))
        return True, current_price 

    return False, current_price



## Defines the overall configuration of the bot 
bot_config = {
    # Name of the bot, as stored in the database
    'name' : 'my_custom_entry_exit_bot',

    # exchange information (fill with your api key and secret)
    'exchange' : {
        'name' : 'kucoin',
        'params' : {
            # 'api_key': '...',
            # 'secret' : '...'
        },
    },

    'timeframe' : '1m',
    'test_run': True,

    # symbols to trade on (all must trade against the same coin, USDT in this case)
    'symbols' : ['SNX/USDT', 'XLM/USDT', 'VET/USDT', 'GO/USDT', 'EOS/USDT', 'ETC/USDT', 'LTC/USDT', 
        'NANO/USDT', 'LYM/USDT', 'TKY/USDT', 'ONT/USDT', 'AOA/USDT', 'SUSD/USDT', 'TRX/USDT', 'BSV/USDT', 
        'DAO/USDT', 'STRONG/USDT', 'TRIAS/USDT', 'MITX/USDT', 'CAKE/USDT', 'KAT/USDT', 'XRP/USDT', 'GRIN/USDT'],

    # starting balance for bot
    'starting_balance' : 10000,

    'strategy': {
        'custom': True,
        'entry_function': customEntryStrategy,
        'exit_function': customExitStrategy,
    },

    'entry_settings' : {
        'trade_amount': 100,
        'signal_distance': 0.2
    },

    'exit_settings' : {
        'exit_on_signal' : True,
    } ,
}


## Runs the bot in an infinite loop, stoppable from the terminal with CTRL + C
def Main():
    bot_controller = defineBot(bot_config)
    while True:
        try:
            bot_controller.executeBot()
            time.sleep(60)
        except KeyboardInterrupt:
            return


if __name__ == '__main__':
    Main()
