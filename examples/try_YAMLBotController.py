import os
from os import getenv
import sys
import time
import glob, importlib
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pprint import pprint
from yaspin import yaspin
from pyjuque.Engine.Models.BotModels import TABotModel as Bot, getSession
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
    bot_model = session.query(Bot).filter_by(name=bot_name).first()
    if bot_model is None:
        print('No bot found by name: {}. Creating...'.format(bot_name))
        InitializeDatabase(session, bot_config)
        Main()

    symbols = []
    if bot_config.__contains__('symbols') is not None:
        symbols = bot_config['symbols']
    strategy  = Strategies[bot_config['strategy']['name']](**bot_config['strategy']['params'])
    bot_controller = BotController(session, bot_model, exchange, strategy)
    status_printer = yaspin()
    bot_controller.status_printer = status_printer

    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        left_to_sleep = bot_config['sleep']
        while left_to_sleep > 0:
            open_orders = bot_controller.bot_model.getOpenOrders(bot_controller.session)
            bot_controller.status_printer.text = "Open Orders: {} | Checking signals in {}".format(len(open_orders), left_to_sleep)
            time.sleep(1)
            left_to_sleep -= 1

if __name__ == '__main__':
    Main()