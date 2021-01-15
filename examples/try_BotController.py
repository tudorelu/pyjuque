import os
import sys
import time
import glob, importlib
from pprint import pprint
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from pprint import pprint
from yaspin import yaspin
from pyjuque.Engine.Models import Base, Bot, Order, Pair, EntrySettings, ExitSettings, getSession
from pyjuque.Engine.Database import InitializeDatabase
from pyjuque.Engine.BotController import BotController, BotInitializer
from pyjuque.Exchanges.Binance import Binance
bot_name = 'bot1'
# db = 'mysql+mysqlconnector://'+os.getenv('DB_USER') +':'\
#     +os.getenv('DB_PASS')+'@'\
#     +os.getenv('DB_HOST')+'/pyjuque'
# session = getSession(db)

def Main():
    symbols = []
    resetOrdersPairs = False
    session = getSession()
    exchange = Binance(get_credentials_from_env=True)
    Strategies = BotInitializer.getStrategies()
    
    bot = session.query(Bot).filter_by(name=bot_name).first()
    if bot is None:
        print('No bot found by name: ' + bot_name + '. Creating...')
        if bot_config['symbols'] is None:
            print('No symbols found in template. Adding all...')
            for symbol in exchange.SYMBOL_DATAS.keys():
                if exchange.SYMBOL_DATAS[symbol]["status"] == "TRADING" \
                    and exchange.SYMBOL_DATAS[symbol]["quoteAsset"] == "BTC":
                    symbols.append(symbol)
        InitializeDatabase(session, symbols, bot_name=bot_name)
        # Restart?
        Main()

    bot_config = BotInitializer.getYamlConfig(bot_name)
    if bot_config['symbols'] is not None:
        symbols = bot_config['strategy']
    strategy  = Strategies[bot_config['strategy']['name']](**bot_config['strategy']['params'])
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