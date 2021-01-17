import os
from os import getenv
import sys
import time
import glob, importlib
from pprint import pprint
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pprint import pprint
from yaspin import yaspin
from pyjuque.Engine.Models.BotModels import TABot as Bot, getSession
from pyjuque.Engine.Database import InitializeDatabase
from pyjuque.Engine.BotController import BotController
from pyjuque.Engine.BotInitializer import getStrategies, getYamlConfig
from pyjuque.Exchanges.CcxtExchange import CcxtExchange

bot_name = 'bot1'

def Main():
    bot_config = getYamlConfig(bot_name)
    
    db_url = None
    if bot_config.__contains__('db_url'):
        db_url = bot_config['db_url']
    
    session = getSession(db_url)
    exchange = CcxtExchange('binance', {
        'apiKey': getenv('BINANCE_API_KEY'), 
        'secret': getenv('BINANCE_API_SECRET'),
        'timeout': 30000,
        'enableRateLimit': True,
    })
    Strategies = getStrategies()

    bot = session.query(Bot).filter_by(name=bot_name).first()
    if bot is None:
        print('No bot found by name: {}. Creating...'.format(bot_name))
        InitializeDatabase(session, bot_config)
        Main()

    symbols = []
    if bot_config.__contains__('symbols') is not None:
        symbols = bot_config['symbols']
    
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
        left_to_sleep = bot_config['time_to_sleep']
        while left_to_sleep > 0:
            bot_controller.sp.text = "Waiting for {} more seconds...".format(left_to_sleep)
            time.sleep(1)
            left_to_sleep -= 1

if __name__ == '__main__':
    Main()