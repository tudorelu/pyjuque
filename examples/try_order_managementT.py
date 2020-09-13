import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from bot.Engine.Models import Base, Bot, Order, Pair
from bot.Engine.OrderManagement import OrderManagement
from pprint import pprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.Strategies.BBRSIStrategy import BBRSIStrategy
from bot.Strategies.EMAXStrategy import EMACrossover
from bot.Strategies.AlwaysBuyStrategy import AlwaysBuyStrategy

from bot.Exchanges.Binance import Binance

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
			starting_balance = 0.001,
			current_balance = 0.001,
			profit_target = 2,
			test_run=False
		)
		session.add(myobject)
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

def Main():

    session = get_session('sqlite:///app.db')
    # First time you run this, uncomment the next line
    initialize_database(session)
    bot = session.query(Bot).filter_by(name='test_bot_2').first()
    exchange = Binance(filename=r'C:\Users\31614\Desktop\pyjuque\pyjuque\bot\Exchanges\credentials.txt')
    strategy = AlwaysBuyStrategy(exchange)
    om = OrderManagement(session, bot, exchange, strategy)
    
    while True:
        try:
            om.execute_bot()
        except KeyboardInterrupt:
                return


if __name__ == '__main__':
		Main()