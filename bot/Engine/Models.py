import sqlalchemy as db
from datetime import datetime
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
import math
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

    id = db.Column(db.String(32), primary_key=True)
    position_id = db.Column(db.Integer, index=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
    symbol = db.Column(db.String(13), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    price = db.Column(SqliteDecimal(13))
    take_profit_price = db.Column(SqliteDecimal(13), default=None)
    entry_price = db.Column(SqliteDecimal(13), default=None)
    stop_price = db.Column(SqliteDecimal(13), default=None)
    original_quantity = db.Column(SqliteDecimal(13))
    executed_quantity = db.Column(SqliteDecimal(13))
    status = db.Column(db.String(30), index=True)
    side = db.Column(db.String(30), index=True)
    is_entry = db.Column(db.Boolean, default=True)
    is_closed = db.Column(db.Boolean, default=False)
    matched_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), default=None)
    is_test = db.Column(db.Boolean)
    order_type = db.Column(db.String(30), index = True)
    last_checked_time = db.Column(db.Integer)

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
  __tablename__ = 'bot'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(30))
  is_running = db.Column(db.Boolean, default=False)
  test_run = db.Column(db.Boolean, default=False)
  quote_asset = db.Column(db.String(10), index=True)
  starting_balance = db.Column(SqliteDecimal(13))
  current_balance = db.Column(SqliteDecimal(13))
  profit_loss = db.Column(db.Float, default=100)
  entry_settings_id = db.Column(db.Integer, db.ForeignKey('entry_settings.id'))
  exit_settings_id = db.Column(db.Integer, db.ForeignKey('exit_settings.id'))

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

  def getFirstBuyOrder(self, session, position_id):
    return session.query(Order).filter_by(bot_id=self.id, position_id=position_id, side='BUY').first()
    
class EntrySettings(Base):
  """
  Model for entry settings
  """

  __tablename__ = 'entry_settings'
  id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
  name = db.Column(db.String(30))                                 # Name (for UI)
  bots = relationship('Bot', backref=backref('entry_settings'))
  open_buy_order_time_out = db.Column(db.Integer, default=math.inf)
  initial_entry_allocation = db.Column(db.Integer, default=None)	# What % of funds allocated to the bot will go to an initial entry
  subsequent_entries = db.Column(db.Integer, default=0)         	# Are there subsequent entries
  subsequent_entry_allocation = db.Column(db.Float, default=1)  	# What % of the initial quantity will we buy on a 
                                  # subsequent entry (1 = 100%, 0.5 = 50%)
  subsequent_entry_distance = db.Column(db.Float, default=None) 	# Distance between subsequent entries in %
  signal_distance = db.Column(db.Float, default=0)         		# Distance from signal for initial entry 
                                    # 0 means enter on signal, 1 means enter 1% away 
                                    # - in the direction opposite that of the trade - 
                                    # from the signal price

class ExitSettings(Base):
    """ Exit Settings of a Bot """
    __tablename__ = 'exit_settings'
    id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
    name = db.Column(db.String(30))                               	# Name for UI
    bots = relationship('Bot', backref=backref('exit_settings'))   # Name (for UI)
    profit_target = db.Column(db.Float)                           	# Exit when price is at value % profit from entry 
    stop_loss_value = db.Column(db.Float, default=None)             	# Whether to have stop loss or not (and what %)
    is_trailing_stop_loss = db.Column(db.Boolean, default=False)    	# Whether to have trailing stop loss or not (what %)
    stop_loss_active_after = db.Column(db.Float, default=None)    	# If we have trailing stop loss, whether to activate immediately, or after a value % increase in profit
    exit_on_signal = db.Column(db.Boolean, default=False)       
