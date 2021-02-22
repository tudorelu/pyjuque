import math
import sqlalchemy as db
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import backref, relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pyjuque.Engine.Models.Utils import SqliteDecimal

Base = declarative_base()

def getScopedSession(path='sqlite:///'):
    some_engine = create_engine(path, echo=False)
    Base.metadata.create_all(some_engine)
    session_factory = sessionmaker(bind=some_engine)
    Session = scoped_session(session_factory)
    return Session

def getSession(path='sqlite:///', default_class=Base):
    some_engine = create_engine(path, echo=False)
    default_class.metadata.create_all(some_engine)
    Session = sessionmaker(bind=some_engine)
    session = Session()
    return session


class OrderModel(Base):
    __tablename__ = 'order'

    id = db.Column(db.String(32), primary_key=True)
    position_id = db.Column(db.Integer, index=True)
    bot_id = db.Column(db.Integer)
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


class PairModel(Base):
    __tablename__ = 'pair'

    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, index=True)
    symbol = db.Column(db.String(13), index=True)
    active = db.Column(db.Boolean, default=True)
    current_order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    profit_loss = db.Column(SqliteDecimal(13), default=1)


class BaseBotModel(Base):

    __abstract__ = True
    __tablename__ = 'base_bot'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))  
    starting_balance = db.Column(SqliteDecimal(13))
    current_balance = db.Column(SqliteDecimal(13))
    profit_loss = db.Column(db.Float, default=100)
    test_run = db.Column(db.Boolean, default=False)

    def getOrders(self, session):
        return session.query(OrderModel).filter_by(bot_id=self.id).all()

    def getOpenOrders(self, session):
        return session.query(OrderModel).filter_by(bot_id=self.id, is_closed=False).all()    


class GridBotModel(BaseBotModel):
    __tablename__ = 'grid_bot'
   
    exchange = db.Column(db.String(30))
    symbol = db.Column(db.String(30))
    trade_amount = db.Column(SqliteDecimal(13))
    trade_step = db.Column(SqliteDecimal(13))


class TABotModel(BaseBotModel):
    __tablename__ = 'ta_bot'

    is_running = db.Column(db.Boolean, default=False)
    quote_asset = db.Column(db.String(10), index=True)
    entry_settings_id = db.Column(db.Integer, db.ForeignKey('entry_settings.id'))
    exit_settings_id = db.Column(db.Integer, db.ForeignKey('exit_settings.id'))

    def getPairs(self, session):
        return session.query(PairModel).filter_by(bot_id=self.id).all()

    def getActivePairs(self, session):
        return session.query(PairModel).filter_by(bot_id=self.id, active=True).all()

    def getPair(self, session, symbol=None):
        if symbol != None:
            return session.query(PairModel).filter_by(bot_id=self.id, symbol=symbol).first()
        return session.query(PairModel).filter_by(bot_id=self.id).first()

    def getFirstBuyOrder(self, session, position_id):
        return session.query(PairModel).filter_by(bot_id=self.id, position_id=position_id, side='BUY').first()
    

class EntrySettingsModel(Base):
    """
    Model for entry settings
    """

    __tablename__ = 'entry_settings'
    id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
    name = db.Column(db.String(30))                                 # Name (for UI)
    bots = relationship('TABotModel', backref=backref('entry_settings'))
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


class ExitSettingsModel(Base):
    """ Exit Settings of a Bot """
    __tablename__ = 'exit_settings'
    id = db.Column(db.Integer, primary_key=True)                  	# Unique ID
    name = db.Column(db.String(30))                               	# Name for UI
    bots = relationship('TABotModel', backref=backref('exit_settings'))   # Name (for UI)
    profit_target = db.Column(db.Float)                           	# Exit when price is at value % profit from entry 
    stop_loss_value = db.Column(db.Float, default=None)             	# Whether to have stop loss or not (and what %)
    is_trailing_stop_loss = db.Column(db.Boolean, default=False)    	# Whether to have trailing stop loss or not (what %)
    stop_loss_active_after = db.Column(db.Float, default=None)    	# If we have trailing stop loss, whether to activate immediately, or after a value % increase in profit
    exit_on_signal = db.Column(db.Boolean, default=False)       
