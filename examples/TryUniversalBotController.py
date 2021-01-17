import sys
import time
from os import getenv
from os.path import abspath, join, pardir
sys.path.append(abspath(join(abspath(__file__), pardir, pardir)))

from pyjuque.Engine.Models.BotModels import TABot as Bot, Order, Pair, EntrySettings, ExitSettings, getSession
from pyjuque.Engine.BotController import BotController
from pprint import pprint
from pyjuque.Strategies.BBRSIStrategy import BBRSIStrategy
from pyjuque.Strategies.AlwaysBuyStrategy import AlwaysBuyStrategy
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from yaspin import yaspin

time_to_sleep = 100

def initialize_database(session, symbols=[]):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    myobject = Bot(
        name="test_bot_ccxt_tudor",
        quote_asset = 'ETH',
        starting_balance = 0.08,
        current_balance = 0.08,
        test_run=False
    )

    session.add(myobject)

    entrysets = EntrySettings(
        initial_entry_allocation = 50,
        # signal_distance = 1,  # in %
        )
    
    exitsets = ExitSettings(
        profit_target = 1,      # in %
        stop_loss_value = 1,   # in %
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
    session = getSession('sqlite:///pyjuque_ccxt_binance_live_1.db')

    exchange = CcxtExchange('binance', {
        'apiKey': getenv('BINANCE_API_KEY'), 
        'secret': getenv('BINANCE_API_SECRET'),
        # 'password': getenv('OKEX_PASSWORD'),
        'timeout': 30000,
        # 'verbose': True,
        'enableRateLimit': True,
    })

    symbols = ['TRX/ETH', 'XRP/ETH']

    # First time you run this, uncomment the next line
    # initialize_database(session, symbols)

    bot = session.query(Bot).filter_by(name='test_bot_ccxt_tudor').first()
    strategy = AlwaysBuyStrategy() # BBRSIStrategy(13, 40, 70, 30)
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