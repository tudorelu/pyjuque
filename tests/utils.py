from pytest import fixture
from pandas import DataFrame, read_csv, to_datetime
import numpy as np

from pyjuque.Strategies import FakeStrategy, MomentumStrategy

from pyjuque.Engine.Models.BotModels import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from time import time


def get_session(path='sqlite:///'):
    some_engine = create_engine(path, echo=False)
    Base.metadata.create_all(some_engine)
    Session = sessionmaker(bind=some_engine)
    session = Session()
    return session


def timeit(function, text=None, *args):
	''' Used to print the time it takes to run a certain function. '''
	start = time()
	ret = function(*args)
	end = time()
	if text is not False:
		if text is None or text == "":
			text = function.__name__+" took "
		print(text+str(round(end - start, 4))+" s")
	return ret, end - start


def assert_exit_price_matches_exit_candle(df, trade):
    exit_price = trade['exit_price']
    exit_candle = df.iloc[trade['end_index']]
    assert exit_price <= exit_candle.high or exit_price >= exit_candle.low, \
        'Trade exit price should be within the high or low of the exit candle'


@fixture
def uniform_df():
    closes = list(range(100, 90, -1)) + list(range(90, 120, 1)) + list(range(120, 100, -1))
    df = DataFrame([closes, closes, closes, closes], ['open', 'high', 'low', 'close']).T
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(np.longdouble)
    df.close = df.close.shift(-1)
    df.close[len(df) - 1] = 100.0
    df.high = df.high + 1.5
    df.low = df.low - 1.5
    df.open = df.open + 0.0
    return df


def long_signal_indices():
    return [100, 130, 200, 230, 300, 330, 400, 430, 500, 600, 700, 800, 900]


def short_signal_indices():
    return [50, 150, 250, 350, 450, 550, 650, 750, 850]


@fixture
def df():
    df = read_csv('./data/BTCUSD_1m_1k.csv')
    df = df.drop('Unnamed: 0', axis=1)
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(np.longdouble)
    df['DateTime'] = to_datetime(df['date'], infer_datetime_format=True)
    return df


@fixture
def long_signals_np(df):
    raw_long_signals = np.zeros(len(df))
    raw_long_signals[long_signal_indices()] = 1
    return raw_long_signals


@fixture
def short_signals_np(df):
    raw_short_signals = np.zeros(len(df))
    raw_short_signals[short_signal_indices()] = 1
    return raw_short_signals


@fixture
def long_signals_df(df):
    raw_long_signals = np.zeros(len(df))
    raw_long_signals[long_signal_indices()] = 1
    return df.iloc[np.where(raw_long_signals == 1)[0]]


@fixture
def short_signals_df(df):
    raw_short_signals = np.zeros(len(df))
    raw_short_signals[short_signal_indices()] = 1
    return df.iloc[np.where(raw_short_signals == 1)[0]]


@fixture
def fake_strat_config(long_signals_np, short_signals_np):
    return dict(
        strategy_class=FakeStrategy,
        strategy_params={
            'long_signals': long_signals_np,
            'short_signals': short_signals_np
        },
    )


def fake_strat_config_manual(long_signals=None, short_signals=None):
    return dict(
        trade_amount = 100,
        strategy_class = FakeStrategy,
        strategy_params = {
            'long_signals': long_signals,
            'short_signals': short_signals
        },
        fee_percent = 0
    )
