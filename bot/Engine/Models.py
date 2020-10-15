import sqlalchemy as db
from datetime import datetime
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base

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

class Order(Base):
		""""""
		__tablename__ = 'order'

		id = db.Column(db.Integer, primary_key=True)
		bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
		symbol = db.Column(db.String(13), index=True)
		timestamp = db.Column(db.DateTime, default=datetime.now)
		entry_price = db.Column(SqliteDecimal(13))
		take_profit_price = db.Column(SqliteDecimal(13), default=None)
		stop_loss_price = db.Column(SqliteDecimal(13), default=None)
		original_quantity = db.Column(SqliteDecimal(13))
		executed_quantity = db.Column(SqliteDecimal(13), default=0)
		status = db.Column(db.String(30))
		side = db.Column(db.String(30))
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
		profit_loss = db.Column(SqliteDecimal(13), default=1)

class Bot(Base):
		""""""
		__tablename__ = 'bot'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(30))
		is_running = db.Column(db.Boolean, default=False)
		test_run = db.Column(db.Boolean, default=False)
		quote_asset = db.Column(db.String(10), index=True)
		starting_balance = db.Column(SqliteDecimal(13))
		current_balance = db.Column(SqliteDecimal(13))
		
		trade_allocation = db.Column(db.Integer, default=50)

		profit_loss = db.Column(db.Float, default=100)
		profit_target = db.Column(SqliteDecimal(13), default=1)
		stop_loss_target = db.Column(SqliteDecimal(13), default=90)

		# pairs = db.relationship('Pair', backref='bot', lazy='dynamic')
		# orders = db.relationship('Order', backref='bot', lazy='dynamic')

		def getActivePairs(self, session):
				return session.query(Pair).filter_by(bot_id=self.id, active=True).all()
			
		def getOpenOrders(self, session):
				return session.query(Order).filter_by(bot_id=self.id, is_closed=False).all()

		def getPairWithSymbol(self, session, symbol):
				return session.query(Pair).filter_by(bot_id=self.id, symbol=symbol).first()


'''
import sqlalchemy as db
from datetime import datetime
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base

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

class Order(Base):
		""""""
		__tablename__ = 'order'

		id = db.Column(db.Integer, primary_key=True)
		bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
		symbol = db.Column(db.String(13), index=True)
		timestamp = db.Column(db.DateTime, default=datetime.now)
		entry_price = db.Column(SqliteDecimal(13))
		original_quantity = db.Column(SqliteDecimal(13))
		executed_quantity = db.Column(SqliteDecimal(13))
		status = db.Column(db.String(30))
		side = db.Column(db.String(30))
		is_test = db.Column(db.Boolean)
		is_entry = db.Column(db.Boolean, default=True)
		is_closed = db.Column(db.Boolean, default=False)
		matched_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), default=None)

class Pair(Base):
		""""""
		__tablename__ = 'pair'

		id = db.Column(db.Integer, primary_key=True)
		bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
		symbol = db.Column(db.String(13), index=True)
		active = db.Column(db.Boolean, default=True)
		current_order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
		profit_loss = db.Column(SqliteDecimal(13), default=1)

class Bot(Base):
		""""""
		__tablename__ = 'bot'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(30))
		is_running = db.Column(db.Boolean, default=False)
		test_run = db.Column(db.Boolean, default=False)
		quote_asset = db.Column(db.String(10), index=True)
		starting_balance = db.Column(SqliteDecimal(13))
		current_balance = db.Column(SqliteDecimal(13))
		profit_loss = db.Column(db.Float, default=100)
		direction = db.Column(db.Bool, default=True)                	# True if LONG, False if SHORT

		def getPairs(self, session):
				return session.query(Pair).filter_by(bot_id=self.id).all()

		def getActivePairs(self, session):
				return session.query(Pair).filter_by(bot_id=self.id, active=True).all()

		def getPairWithSymbol(self, session, symbol):
				return session.query(Pair).filter_by(bot_id=self.id, symbol=symbol).first()

		def getOrders(self, session):
				return session.query(Order).filter_by(bot_id=self.id).all()
	
		def getOpenOrders(self, session):
				return session.query(Order).filter_by(bot_id=self.id, is_closed=False).all()

class EntrySettings(Base):
	""" Entry Settings of a Bot """
	id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
	name = db.Column(db.String(30))                               	# Name (for UI)
	bots = db.relationship('Bot', backref='entry_settings', lazy='dynamic')
	initial_entry_allocation = db.Column(db.Integer, default=None)	# What % of funds allocated to the bot will go
	                                                              	# to an initial entry
	subsequent_entries = db.Column(db.Integer, default=0)         	# Are there subsequent entries
	subsequent_entry_allocation = db.Column(db.Float, default=1)  	# What % of the initial quantity will we buy on a 
	                                                              	# subsequent entry (1 = 100%, 0.5 = 50%)
	subsequent_entry_distance = db.Column(db.Float, default=None) 	# Distance between subsequent entries in %
	signal_distance = db.Column(db.Float, default=None)         		# Distance from signal for initial entry 
	                                                            		# None means enter on signal, 1 means enter 1% away 
	                                                            		# - in the direction opposite that of the trade - 
	                                                            		# from the signal price

class ExitSettings(Base):
	""" Exit Settings of a Bot """
	id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
	name = db.Column(db.String(30))                               	# Name for UI
	bots = db.relationship('Bot', backref='exit_settings', lazy='dynamic')
	profit_target = db.Column(db.Float)                           	# Exit when price is at value % profit from entry 
	stop_loss_value = db.Column(db.Float, default=None)             	# Whether to have stop loss or not (and what %)
	is_trailing_stop_loss = db.Column(db.Boolean, default=False)    	# Whether to have trailing stop loss or not (what %)
	stop_loss_active_after = db.Column(db.Float, default=None)    	# If we have trailing stop loss, whether to activate 
	                                                              	# immediately, or after a value % increase in profit

'''