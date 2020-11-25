import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

import time

from pyjuque.Engine.Models import Base, Bot, Order, Pair, EntrySettings, ExitSettings, getSession
from pyjuque.Engine.BotController import BotController
from pprint import pprint

from pyjuque.Strategies.EMAXStrategy import EMACrossover
from pyjuque.Strategies.BBRSIStrategy import BBRSIStrategy
from pyjuque.Strategies.AlwaysBuyStrategy import AlwaysBuyStrategy

from pyjuque.Exchanges.Binance import Binance

from yaspin import yaspin

time_to_sleep = 10

def initialize_database(session, symbols=[]):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    myobject = Bot(
        name="test_bot_2",
        quote_asset = 'BTC',
        starting_balance = 0.1,
        current_balance = 0.1,
        test_run=True
    )

    session.add(myobject)

    entrysets = EntrySettings(
        id = 1,
        name ='TimStoploss',
        initial_entry_allocation = 0.01,
        signal_distance = 0.2,  # in %
        )
    exitsets = ExitSettings(
        id=1,
        name='TimLoss',
        profit_target = 1,      # in %
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

def clearOrdersFromDB(session):
    session.query(Order).delete()
    session.query(Pair).delete()
    session.commit()
    pair = Pair(
        bot_id = 1,
        symbol = "NEOBTC",
        current_order_id = None
    )
    pair_2 = Pair(
        bot_id = 1,
        symbol = "BNBBTC",
        current_order_id = None
    )
    session.add(pair)
    session.add(pair_2)
    session.commit()

def Main():
    resetOrdersPairs = False
    session = getSession('sqlite:///pyjuque_test_3.db')

    exchange = Binance()

    symbols = []
    for symbol in exchange.SYMBOL_DATAS.keys():
        if exchange.SYMBOL_DATAS[symbol]["status"] == "TRADING" \
            and exchange.SYMBOL_DATAS[symbol]["quoteAsset"] == "BTC":
            symbols.append(symbol)

    # First time you run this, uncomment the next line
    # initialize_database(session, symbols)

    if resetOrdersPairs:
        clearOrdersFromDB(session)

    bot = session.query(Bot).filter_by(name='test_bot_2').first()
    # input your path to credentials here.

    # strategy = AlwaysBuyStrategy()
    strategy = BBRSIStrategy(13, 40, 70, 30)
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
        bot_controller.sp.text = "Waiting for {} seconds...".format(time_to_sleep)
        time.sleep(time_to_sleep)

if __name__ == '__main__':
        Main()