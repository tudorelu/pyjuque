import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, sessionmaker, scoped_session
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


class CandlestickModel(Base):
    __tablename__ = 'candlestick'
    symbol = db.Column(db.String(13), index=True, primary_key=True)
    timeframe = db.Column(db.String(5), index=True, primary_key=True)
    timestamp = db.Column(db.String, index=True, primary_key=True)
    datetime = db.Column(db.DateTime)
    open = db.Column(db.String)
    high = db.Column(db.String)
    low = db.Column(db.String)
    close = db.Column(db.String)
    volume = db.Column(db.String)