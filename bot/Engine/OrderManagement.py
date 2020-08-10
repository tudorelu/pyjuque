# This is the class that handles the actual buying and selling.
# Basic version: 
# 		Buy when we receive a buy signal from strategy.
#  		Sell when we hit our profit target (% increase from buy price)

import sqlalchemy as db
from datetime import datetime
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base

import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)


Base = declarative_base()

class SqliteDecimal(types.TypeDecorator):
	# This TypeDecorator use Sqlalchemy Integer as impl. It converts Decimals
	# from Python to Integers which is later stored in Sqlite database.
	impl = types.BigInteger

	def __init__(self, scale):
		# It takes a 'scale' parameter, which specifies the number of digits
		# to the right of the decimal point of the number in the column.
		types.TypeDecorator.__init__(self)
		self.scale = scale
		self.multiplier_int = 10 ** self.scale

	def process_bind_param(self, value, dialect):
		# e.g. value = Column(SqliteDecimal(2)) means a value such as
		# Decimal('12.34') will be converted to 1234 in Sqlite
		if value is not None:
			value = int(Decimal(value) * self.multiplier_int)
		return value

	def process_result_value(self, value, dialect):
		# e.g. Integer 1234 in Sqlite will be converted to SqliteDecimal('12.34'),
		# when query takes place.
		if value is not None:
			value = Decimal(value) / self.multiplier_int
		return value

#from sqlalchemy import Integer, String, Decimal, Boolean, DateTime, Column
class Order(Base):
		""""""
		__tablename__ = 'order'

		id = db.Column(db.Integer, primary_key=True)
		bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
		symbol = db.Column(db.String(13), index=True)
		timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
		entry_price = db.Column(SqliteDecimal(9))
		take_profit_price = db.Column(SqliteDecimal(9), default=None)
		stop_loss_price = db.Column(SqliteDecimal(9), default=None)
		original_quantity = db.Column(SqliteDecimal(9))
		executed_quantity = db.Column(SqliteDecimal(9))
		status = db.Column(db.String(30), index=True)
		side = db.Column(db.String(30), index=True)
		is_entry = db.Column(db.Boolean, default=True)
		is_closed = db.Column(db.Boolean, default=False)
		matched_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), default=None)
		is_test = db.Column(db.Boolean)


class Pair(Base):
		""""""
		__tablename__ = 'pair'

		id = db.Column(db.Integer, primary_key=True)
		bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
		symbol = db.Column(db.String(13), index=True)
		active = db.Column(db.Boolean, default=True)
		current_order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
		profit_loss = db.Column(SqliteDecimal(9), default=1)

class Bot(Base):
		""""""
		__tablename__ = 'bot'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(30))
		is_running = db.Column(db.Boolean, default=False)
		test_run = db.Column(db.Boolean, default=False)
		quote_asset = db.Column(db.String(10), index=True)
		starting_balance = db.Column(SqliteDecimal(9))
		current_balance = db.Column(SqliteDecimal(9))
		
		trade_allocation = db.Column(db.Integer, default=50)

		profit_loss = db.Column(SqliteDecimal(9), default=100)
		profit_target = db.Column(SqliteDecimal(9), default=100)

		# pairs = db.relationship('Pair', backref='bot', lazy='dynamic')
		# orders = db.relationship('Order', backref='bot', lazy='dynamic')

		def getActiveSymbols(self):
				return Pair.query.filter_by(bot_id=self.id, active=True).all()
			
		def getOpenOrders(self):
				return Order.query.filter_by(bot_id=self.id, is_closed=False).all()

		def getPairOfSymbol(self, symbol):
				return Pair.query.filter_by(bot_id=self.id, symbol=symbol).first()
  			
## CONNECT TO A DB SESSION (INITIALIZE)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def initialize_database():
		# an Engine, which the Session will use for connection resources

		some_engine = create_engine('sqlite:///app.db', echo=True)

		Base.metadata.create_all(some_engine)

		# create a configured "Session" class
		Session = sessionmaker(bind=some_engine)

		# create a Session
		session = Session()

		# work with sess
		myobject = Bot(
			name="test_bot2",
			quote_asset = 'BNB',
			starting_balance = 1,
			current_balance = 1
		)
		session.add(myobject)
		session.commit()



from bot.Exchanges.Binance import Binance
from pandas import DataFrame

from bot.Strategies.BBRSIStrategy import BBRSIStrategy


# 1. Retreive all paris for a particular bot

# 2. For Each Pair:
		#		Retreive current market data 
		# 	Compute Indicators & Check if Strategy is Fulfilled
		#		IF Fulfilled, palce order (Save order in DB)

# 3. Retreive all open orders on the bot

# 4. For Each order that was already placed by the bot and was not filled
		#		Check status 
		#		IF FIlled -> If entry order, place exit order
		#							-> If Exit order, SUCCESS (or failure:( ) Resume trading!

def bot_loop(bot, strategy_function):
		""" """
		try:
				# Step 1
				active_symbols = bot.getActiveSymbols()

				# Step 2
				for symbol in active_symbols:
						try_entry_order(bot_state, symbol)

				# Step 3
				open_orders = bot.getOpenOrders()

				# Step 4
				for order in open_orders:
						try_exit_order(bot_state, order)
		except:
				pass

def try_entry_order(bot:Bot, symbol:str, strategy_function:BBRSIStrategy):
		""" """
		binance = Binance()
		df = binance.getSymbolKlines(symbol, "5m", limit=100)
		strat = BBRSIStrategy(df, 8, 100, 60, 40)
		l = len(df) - 1
		buy_signal = strat.checkBuySignal(l)
		
		if buy:
				take_profit = bot.profit_target
				desired_price = df['close'][l]
				quote_qty =  Decimal(bot.starting_balance) * Decimal(bot.trade_allocation) / Decimal(100)
				desired_quantity = quote_qty / desired_price
				order = Order(
						bot_id = bot.id, 
						symbol = symbol,
						status = "NEW", 
						side = "BUY", 
						is_entry = True, 
						entry_price=desired_price, 
						original_quantity = desired_quantity,
						executed_quantity = 0,
						is_closed = False, 
						is_test = bot.test_run)

				db.session.add(order)
				db.session.commit()
				
				order_response = dict()
				if bot.test_run:
						order_response = exchange.placeLimitOrder(
								symbol=symbol, 
								price=desired_price, 
								side="BUY",
								test=True,
								amount=desired_quantity,
								custom_id=order.id)
				else:
						order_response = exchange.placeLimitOrder(
								symbol=symbol, 
								price=desired_price, 
								side="BUY",
								amount=desired_quantity,
								custom_id=order.id)

				if exchange.isValidResponse(order_response):
						bot.current_balance = bot.current_balance - quote_qty
						exchange.updateSQLOrderModel(order, order_response)
						pair = bot.getPairOfSymbol(symbol)
						pair.current_order_id = order.id
						pair.active = False
						db.session.commit()
				else:
						db.session.query(Order).filter(Order.id==order.id).delete()
						db.session.commit()


def try_exit_order(bot:Bot, order):
		""" """
		symbol = order.symbol
		
		exchange = Binance()
		pair:Pair = bot.getPairOfSymbol(symbol)
		order:Order = Order.query.get(order.id)

		if order.is_test:
			df = exchange.getSymbolKlines(order.symbol, '5m', 50)
			l = len(df) - 1
			filled = False

			for index, row in df.iterrows():
				if datetime.fromtimestamp(row['time']/1000) > order.timestamp:
					if order.is_entry:
						if row['low'] < order.entry_price:
							order.status = exchange.ORDER_STATUS_FILLED
							order.executed_quantity = order.original_quantity
							order.is_closed = True
							filled = True
							db.session.commit()
							break	

					elif not order.is_entry:
						if row['high'] > Decimal(order.entry_price):
							order.status = exchange.ORDER_STATUS_FILLED
							order.executed_quantity = order.original_quantity
							order.is_closed = True
							filled = True
							db.session.commit()	
							break

		else:
			exchange_order_info = exchange.getOrderInfo(symbol, order.id)
			if not exchange.isValidResponse(exchange_order_info):
				return
			order.status = exchange_order_info['status']
			order.executed_quantity = exchange_order_info['executedQty']
		
		db.session.commit()

		if order.status == exchange.ORDER_STATUS_FILLED:
			if order.is_entry:
  				
				# If this entry order has been filled
				new_order_model = Order(
					bot_id = bot.id,
					symbol = symbol,
					status = "NEW",
					side = "SELL", 
					is_entry = False, 
					entry_price=order.take_profit_price, 
					original_quantity=order.executed_quantity,
					executed_quantity = 0,
					is_closed = False, 
					is_test = bot.test_run)

				db.session.add(new_order_model)
				db.session.commit()

				exit_price = order.take_profit_price
				
				new_order_response = dict(message="success")
				if bot.test_run:
					new_order_response = exchange.placeLimitOrder(
						symbol = symbol, 
						price = exit_price,
						side = "SELL",
						amount = order.executed_quantity,
						test = bot.test_run,
						custom_id=new_order_model.id)
				else:
					new_order_response = exchange.placeLimitOrder(
						symbol = symbol, 
						price = exit_price,
						side = "SELL",
						amount = order.executed_quantity,
						custom_id=new_order_model.id)
					
				if exchange.isValidResponse(new_order_response):
					exchange.updateSQLOrderModel(new_order_model, new_order_response, bot)
					new_order_model.matched_order_id = order.id
					order.is_closed = True
					order.matched_order_id = new_order_model.id
					pair.active = False
					pair.current_order_id = new_order_model.id
					db.session.commit()
				else:
					db.session.query(Order).filter(Order.id==new_order_model.id).delete()
					db.session.commit()
			
			else:
				order.is_closed = True
				pair.active = True
				pair.current_order_id = None
				db.session.commit()

		# If the order has been cancelled, set the order to close and start from beginning
		elif order.status == exchange.ORDER_STATUS_CANCELED:
			order.is_closed = True
			pair.active = True
			pair.current_order_id = None
			db.session.commit()

def create_bot():
		some_engine = create_engine('sqlite:///app.db', echo=True)
		Base.metadata.create_all(some_engine)
		Session = sessionmaker(bind=some_engine)
		session = Session()
		myobject = Bot(
			name="test_bot_3",
			quote_asset = 'BTC',
			starting_balance = 1,
			current_balance = 1,
			profit_target = 2
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

		create_bot()
		# some_engine = create_engine('sqlite:///app.db', echo=True)
		# Base.metadata.create_all(some_engine)
		# Session = sessionmaker(bind=some_engine)
		# session = Session()

		# session.query


		# while(True):
  	# 		bot_loop()


if __name__ == '__main__':
		Main()