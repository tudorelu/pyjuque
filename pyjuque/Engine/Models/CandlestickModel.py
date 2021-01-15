import sqlalchemy as db
from datetime import datetime
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy import create_engine
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from pyjuque.Engine.Models.Utils import SqliteDecimal

Base = declarative_base()

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
    timestamp = db.Column(db.Integer, index=True, primary_key=True)
    open = db.Column(SqliteDecimal(13))
    high = db.Column(SqliteDecimal(13))
    low = db.Column(SqliteDecimal(13))
    close = db.Column(SqliteDecimal(13))
    volume = db.Column(SqliteDecimal(13))