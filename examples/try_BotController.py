import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pyjuque.Engine.Models import Base, Bot, Order, Pair, EntrySettings, ExitSettings
from pyjuque.Engine.BotController import BotController
from pprint import pprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pyjuque.Strategies.EMAXStrategy import EMACrossover
from pyjuque.Strategies.AlwaysBuyStrategy import AlwaysBuyStrategy

from pyjuque.Exchanges.Binance import Binance

def get_session(path='sqlite:///'):
    some_engine = create_engine(path, echo=False)
    Base.metadata.create_all(some_engine)
    Session = sessionmaker(bind=some_engine)
    session = Session()
    return session

def initialize_database(session):
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
        id =1,
        name ='TimStoploss',
        initial_entry_allocation=1,
        signal_distance = -1,
        )
    exitsets = ExitSettings(
                            id=1,
                            name='TimLoss',
                            profit_target=1,
                            stop_loss_value=0,
                            exit_on_signal=True
                            )
    myobject.entry_settings = entrysets
    myobject.exit_settings = exitsets
    session.commit()
    pair = Pair(
        bot_id = myobject.id,
        symbol = "NEOBTC",
        current_order_id = None
    )
    pair_2 = Pair(
        bot_id = myobject.id,
        symbol = "BNBBTC",
        current_order_id = None
    )
    session.add(pair)
    session.add(pair_2)
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
    session = get_session('sqlite:///pyjuquetest1.db')
    # First time you run this, uncomment the next line
    # initialize_database(session)
    if resetOrdersPairs:
        clearOrdersFromDB(session)

    bot = session.query(Bot).filter_by(name='test_bot_2').first()
    # input your path to credentials here.
    exchange = Binance(get_credentials_from_env=True)
    strategy = AlwaysBuyStrategy()
    om = BotController(session, bot, exchange, strategy)

    while True:
        try:
            om.executeBot()
        except KeyboardInterrupt:
            return


if __name__ == '__main__':
        Main()