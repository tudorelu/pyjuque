import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from bot.Engine.Models import Base, Bot, Order, Pair
from bot.Engine.OrderManagement import execute_bot
from pprint import pprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.Strategies.BBRSIStrategy import BBRSIStrategy
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
			name="test_bot_3",
			quote_asset = 'BTC',
			starting_balance = 1,
			current_balance = 1,
			profit_target = 2,
			test_run=True
		)
		session.add(myobject)
		session.commit()
		pair = Pair(
			bot_id = myobject.id,
			symbol = "ETHBTC",
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
		""" """
		session = get_session('sqlite:///app.db')
		# First time you run this, uncomment the next line
		# initialize_database(session)
		bot = session.query(Bot).filter_by(name='test_bot_3').first()
		exchange = Binance()

		while True:
				try:
						execute_bot(
							session=session, 
							bot=bot, 
							exchange=exchange, 
							strategy=AlwaysBuyStrategy()) #BBRSIStrategy(8, 100, 60, 40))
				except KeyboardInterrupt:
						return


if __name__ == '__main__':
		Main()