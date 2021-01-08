import os
import sys
import time
import glob, importlib
from os.path import dirname, basename, isfile, join
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from pprint import pprint
from yaspin import yaspin
from pyjuque.Engine.Models_mysql import Base, Bot, Order, Pair, EntrySettings, ExitSettings, getSession
from pyjuque.Engine.BotController import BotController

Strategies = {}
__globals = globals()
for path in glob.glob('pyjuque/Strategies/[!_]*.py'):
    path, file = os.path.split(path)
    mod_name = file[:-3]
    if mod_name != 'BaseStrategy':
        mod_path = path.replace("/", ".") +'.' + mod_name
        Strategies[mod_name] = getattr(importlib.import_module(mod_path), mod_name)

from pyjuque.Exchanges.Binance import Binance

time_to_sleep = 10
bot_name = 'bot1'
symbols = ['ETHBTC', 'ZILBTC', 'BTCUSDT', 'MKRBTC','ETCBTC','SNXBTC']


def initialize_database(session, symbols=[]):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    myobject = Bot(
        name=bot_name,
        quote_asset = 'BTC',
        starting_balance = 0.001,
        current_balance = 0.001,
        test_run=False
    )

    session.add(myobject)

    entrysets = EntrySettings(
        id = 1,
        name ='TimStoploss',
        initial_entry_allocation = 30,
        signal_distance = 1,  # in %
        )
    
    exitsets = ExitSettings(
        id=1,
        name='TimLoss',
        profit_target = 3,      # in %
        stop_loss_value = 10,   # in %
        exit_on_signal=False
        )
    myobject.entry_settings = entrysets
    myobject.exit_settings = exitsets
    session.commit()

    for symbol in symbols:
        pair = Pair(
            bot_id = myobject.id,
            symbol = symbol,
            current_order_id = None
        )
        session.add(pair)

    session.commit()

def Main():
    resetOrdersPairs = False
    # session = getSession('sqlite:///db/' + db_name)
    db = 'mysql+mysqlconnector://'+os.getenv('DB_USER') +':'\
        +os.getenv('DB_PASS')+'@'\
        +os.getenv('DB_HOST')+'/pyjuque'
        
    session = getSession(db)
    exchange = Binance(get_credentials_from_env=True)
    
    # Add all symbols on exchange
    # for symbol in exchange.SYMBOL_DATAS.keys():
    #     if exchange.SYMBOL_DATAS[symbol]["status"] == "TRADING" \
    #         and exchange.SYMBOL_DATAS[symbol]["quoteAsset"] == "BTC":
    #         symbols.append(symbol)
    # First time you run this, uncomment the next line
    #initialize_database(session, symbols)

    bot = session.query(Bot).filter_by(name=bot_name).first()
    print('Available Strategies:')
    print('')
    for strategy in Strategies:
        print(strategy)

    # strategy = AlwaysBuyStrategy()
    # strategy = BBRSIStrategy(13, 40, 70, 30)
    strategy  = Strategies['BBRSIStrategy'](13, 40, 70, 30)

    bot_controller = BotController(session, bot, exchange, strategy)
    sp = yaspin()
    bot_controller.sp = sp
    bot_controller.sp_on = True
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        bot_controller.sp.start()
        left_to_sleep = time_to_sleep
        while left_to_sleep > 0:
            bot_controller.sp.text = "Waiting for {} more seconds...".format(left_to_sleep)
            time.sleep(1)
            left_to_sleep -= 1

if __name__ == '__main__':
    Main()