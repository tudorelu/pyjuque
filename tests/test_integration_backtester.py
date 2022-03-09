""" The following contains a series integration tests on the backtester
    made on a synthetic dataframe where the prices are uniform/ linear
    (from 100 they go down to 90, up to 120 and back down to 100)

uniform_df:
        open   high    low  close
    0   100.0  101.5   98.5   99.0
    1    99.0  100.5   97.5   98.0
    2    98.0   99.5   96.5   97.0
    3    97.0   98.5   95.5   96.0
    4    96.0   97.5   94.5   95.0
    5    95.0   96.5   93.5   94.0
    6    94.0   95.5   92.5   93.0
    7    93.0   94.5   91.5   92.0
    8    92.0   93.5   90.5   91.0
    9    91.0   92.5   89.5   90.0
    10   90.0   91.5   88.5   91.0
    11   91.0   92.5   89.5   92.0
    12   92.0   93.5   90.5   93.0
    13   93.0   94.5   91.5   94.0
    14   94.0   95.5   92.5   95.0
    15   95.0   96.5   93.5   96.0
    16   96.0   97.5   94.5   97.0
    17   97.0   98.5   95.5   98.0
    18   98.0   99.5   96.5   99.0
    19   99.0  100.5   97.5  100.0
    20  100.0  101.5   98.5  101.0
    21  101.0  102.5   99.5  102.0
    22  102.0  103.5  100.5  103.0
    23  103.0  104.5  101.5  104.0
    24  104.0  105.5  102.5  105.0
    25  105.0  106.5  103.5  106.0
    26  106.0  107.5  104.5  107.0
    27  107.0  108.5  105.5  108.0
    28  108.0  109.5  106.5  109.0
    29  109.0  110.5  107.5  110.0
    30  110.0  111.5  108.5  111.0
    31  111.0  112.5  109.5  112.0
    32  112.0  113.5  110.5  113.0
    33  113.0  114.5  111.5  114.0
    34  114.0  115.5  112.5  115.0
    35  115.0  116.5  113.5  116.0
    36  116.0  117.5  114.5  117.0
    37  117.0  118.5  115.5  118.0
    38  118.0  119.5  116.5  119.0
    39  119.0  120.5  117.5  120.0
    40  120.0  121.5  118.5  119.0
    41  119.0  120.5  117.5  118.0
    42  118.0  119.5  116.5  117.0
    43  117.0  118.5  115.5  116.0
    44  116.0  117.5  114.5  115.0
    45  115.0  116.5  113.5  114.0
    46  114.0  115.5  112.5  113.0
    47  113.0  114.5  111.5  112.0
    48  112.0  113.5  110.5  111.0
    49  111.0  112.5  109.5  110.0
    50  110.0  111.5  108.5  109.0
    51  109.0  110.5  107.5  108.0
    52  108.0  109.5  106.5  107.0
    53  107.0  108.5  105.5  106.0
    54  106.0  107.5  104.5  105.0
    55  105.0  106.5  103.5  104.0
    56  104.0  105.5  102.5  103.0
    57  103.0  104.5  101.5  102.0
    58  102.0  103.5  100.5  101.0
    59  101.0  102.5   99.5  100.0

"""

from pprint import pprint
from copy import deepcopy
from .utils import (df, long_signals_np, short_signals_np, fake_strat_config, 
    long_signal_indices, short_signal_indices, MomentumStrategy, uniform_df,
    fake_strat_config_manual, assert_exit_price_matches_exit_candle)
from pyjuque.Backtester import Backtester
from pytest import raises
import numpy as np
from math import isclose
# from pyjuque.backtester.Exceptions import InvalidBacktesterConfigError

# - check that we enter / exit on the *precise* candles on which we are supposed to 
# - that the fees are subtracted properly, 
# - that the PNL and DD are what we expect


# Creates a backtester object given a backtester config object and a dataframe
def compute_backtest_results(df, config):
    bt = Backtester(config=config)
    bt.backtest(df)
    res = bt.get_results()
    return bt


# Encapsulates assertions about a given backtester object
def assert_bt_state(bt, e_equity=None, e_dd=None, e_pnl=None, 
    e_max_drawdown=None, e_n_trades=None, e_n_wins=None, 
    e_n_losses=None, e_n_longs=None, e_n_shorts=None, e_length=None):
    if not e_equity is None:
        assert isclose(bt.equity[-1], e_equity, abs_tol=1e-15), \
            f'Should have {e_equity} Equity at the end'
    if not e_dd is None:
        assert isclose(bt.drawdown[-1], e_dd, abs_tol=1e-15), \
            f'Should have {e_dd} final DD'
    if not e_pnl is None:
        assert isclose(bt.pnl[-1], e_pnl, abs_tol=1e-15), \
            f'Should have {e_pnl} PNL'
    if not e_max_drawdown is None:
        assert isclose(bt.max_drawdown, e_max_drawdown, abs_tol=1e-15), \
            f'Should have {e_max_drawdown} Max DD'
    if not e_n_trades is None:
        assert bt.n_trades == e_n_trades, f'Should have {e_n_trades} trades'
        assert len(bt.trades) == e_n_trades, \
            f'Should have {e_n_trades} length of trades array'
    if not e_n_wins is None:
        assert bt.n_wins == e_n_wins, f'Should have {e_n_wins} wins'
    if not e_n_losses is None:
        assert bt.n_losses == e_n_losses, f'Should have {e_n_losses} losses'
    if not e_n_longs is None:
        assert bt.n_longs == e_n_longs, f'Should have {e_n_longs} longs'
    if not e_n_shorts is None:
        assert bt.n_shorts == e_n_shorts, f'Should have {e_n_shorts} shorts'
    assert len(bt.pnl) == e_length, \
        f'PNL length should be equal to {e_length}'
    assert len(bt.drawdown) == e_length, \
        f'DD length should be equal to {e_length}'
    assert len(bt.equity) == e_length, \
        f'DD length should be equal to {e_length}'


def test_one_trade_take_profit_long_only(uniform_df):
    buy_indices = np.where(uniform_df.open == 100)[0]
    long_signals = np.zeros(len(uniform_df))
    long_signals[buy_indices] = 1
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    config['take_profit_value'] = 10
    bt = compute_backtest_results(uniform_df, config)
    assert_bt_state(bt, e_pnl = 0.1, e_equity = 110, e_max_drawdown = 0.1, 
        e_n_trades = 1, e_n_wins = 1, e_n_losses = 0, e_n_longs = 1, e_n_shorts = 0, 
        e_length = len(uniform_df))
    trade = bt.trades[0]
    assert_exit_price_matches_exit_candle(uniform_df, trade)
    assert uniform_df.iloc[trade['start_index']].open == 100, 'Should have bought at $100'
    assert uniform_df.iloc[trade['end_index']].high > 110, 'Should have sold at $110'


def test_one_trade_stop_loss_long_only(uniform_df):
    buy_indices = np.where(uniform_df.open == 100)[0]
    long_signals = np.zeros(len(uniform_df))
    # Only on the first candle we have a buy signal
    long_signals[buy_indices[:1]] = 1
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    config['stop_loss_value'] = 10
    bt = compute_backtest_results(uniform_df, config)
    assert_bt_state(bt, e_pnl = -0.1, e_equity = 90, e_dd = -0.1, e_max_drawdown = 0.1, 
        e_n_trades = 1, e_n_wins = 0, e_n_losses = 1, e_n_longs = 1, e_n_shorts = 0, 
        e_length = len(uniform_df))
    trade = bt.trades[0]
    assert_exit_price_matches_exit_candle(uniform_df, trade)
    assert uniform_df.iloc[trade['start_index']].open == 100, 'Should have bought at $100'
    assert uniform_df.iloc[trade['end_index']].low < 90, 'Should have sold at $110'


def test_two_trades_take_profit_and_stop_loss_long_only(uniform_df):
    buy_indices = np.where(uniform_df.open == 100)[0]
    long_signals = np.zeros(len(uniform_df))
    long_signals[buy_indices] = 1
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    config['stop_loss_value'] = 10
    config['take_profit_value'] = 10
    bt = compute_backtest_results(uniform_df, config)
    print(bt.pnl)
    print(bt.equity)
    print(bt._get_tp_price(100, 1))
    pprint(bt.trades)
    pprint(bt.idx_take_profit)
    assert_bt_state(bt, e_pnl = 0, e_equity = 100, e_max_drawdown = 0.1, 
        e_n_trades = 2, e_n_wins = 1, e_n_losses = 1, e_n_longs = 2, e_n_shorts = 0, 
        e_length = len(uniform_df))
    assert isclose(bt.profit_net[-1], 0, abs_tol=1e-09), 'Should have $0 Profit Net at the end'
    trade = bt.trades[0]
    assert_exit_price_matches_exit_candle(uniform_df, trade)
    assert uniform_df.iloc[trade['start_index']].open == 100, 'Should have bought at $100'
    assert uniform_df.iloc[trade['end_index']].low < 90, 'Should have sold at $110'
    trade = bt.trades[1]
    assert_exit_price_matches_exit_candle(uniform_df, trade)
    assert uniform_df.iloc[trade['start_index']].open == 100, 'Should have bought at $100'
    assert uniform_df.iloc[trade['end_index']].high > 110, 'Should have sold at $110'


def test_one_trade_take_profit_short_only(uniform_df):
    sell_indices = np.where(uniform_df.open == 100)[0]
    short_signals = np.zeros(len(uniform_df))
    short_signals[sell_indices[:1]] = 1
    config = deepcopy(fake_strat_config_manual(short_signals=short_signals))
    config['go_short'] = True
    config['take_profit_value'] = 10
    bt = compute_backtest_results(uniform_df, config)
    assert_bt_state(bt, e_pnl = 0.1, e_equity = 110, e_dd = 0, e_max_drawdown = 0, 
        e_n_trades = 1, e_n_wins = 1, e_n_losses = 0, e_n_longs = 0, e_n_shorts = 1, 
        e_length = len(uniform_df))
    trade = bt.trades[0]
    assert_exit_price_matches_exit_candle(uniform_df, trade)
    assert uniform_df.iloc[trade['start_index']].open == 100, 'Should have bought at $100'
    assert uniform_df.iloc[trade['end_index']].low < 90, 'Should have sold at $110'


def test_multiple_trades_percent_take_profit_long_only(uniform_df):
    long_signals = np.zeros(len(uniform_df))
    long_signals[[10, 20, 30]] = 1
    assert len(np.where(long_signals==1)[0]) == 3, 'Should have 3 buy indices'
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    for percent_profit in [2, 2.1, 2.222, 2.123, 2.3456789, 3, 4, 4.154, 5, 8]:
        config['take_profit_value'] = percent_profit
        bt = compute_backtest_results(uniform_df, config)
        assert_bt_state(bt, e_pnl = (percent_profit * 3) / 100,
            e_dd = 0, e_max_drawdown=0, e_n_trades=3, e_n_wins=3, e_n_losses=0,
            e_n_longs=3, e_n_shorts=0, e_length=len(uniform_df))
        for trade in bt.trades:
            assert trade['is_win'], 'Should be a winning trade'
            assert trade['is_long'], 'Should be a long trade'
            assert isclose(100 * (trade['exit_price'] / trade['entry_price'] - 1), percent_profit), \
                f'Should have a %{percent_profit} diff between exit and entry prices'
            assert_exit_price_matches_exit_candle(uniform_df, trade)


def test_multiple_trades_percent_take_profit_short_only(uniform_df):
    short_signals = np.zeros(len(uniform_df))
    short_signals[[0, 40, 50]] = 1
    assert len(np.where(short_signals==1)[0]) == 3, 'Should have 3 sell indices'
    config = deepcopy(fake_strat_config_manual(short_signals=short_signals))
    config['go_short'] = True
    for percent_profit in [2, 2.1, 2.222, 2.123, 2.3456789, 3, 4, 4.154, 5, 8]:
        config['take_profit_value'] = percent_profit
        bt = compute_backtest_results(uniform_df, config)
        assert_bt_state(bt, e_pnl = (percent_profit * 3) / 100,
            e_dd = 0, e_max_drawdown = 0, e_n_trades = 3, e_n_wins = 3, e_n_losses = 0,
            e_n_longs = 0, e_n_shorts = 3, e_length = len(uniform_df))
        for trade in bt.trades:
            assert trade['is_win'], 'Should be a winning trade'
            assert not trade['is_long'], 'Should be a short trade'
            assert isclose(100 * (1 - trade['exit_price'] / trade['entry_price']), percent_profit), \
                f'Should have a %{percent_profit} diff between exit and entry prices'
            assert_exit_price_matches_exit_candle(uniform_df, trade)


def test_multiple_trades_fixed_take_profit_long_only(uniform_df):
    long_signals = np.zeros(len(uniform_df))
    long_signals[[10, 20, 30]] = 1
    assert len(np.where(long_signals==1)[0]) == 3, 'Should have 3 buy indices'
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    for fixed_profit in [2, 2.1, 2.222, 2.123, 2.3456789, 3, 4, 5, 8, 9, 10]:
        config['take_profit_value'] = fixed_profit
        config['take_profit_type'] = 'fixed' # 'fixed' or 'percent
        bt = compute_backtest_results(uniform_df, config)
        assert_bt_state(bt, e_dd = 0, e_max_drawdown = 0, e_n_trades = 3, e_n_wins = 3, 
            e_n_losses = 0, e_n_longs = 3, e_n_shorts = 0, e_length = len(uniform_df))
        for trade in bt.trades:
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            exit_candle = uniform_df.iloc[trade['end_index']]
            assert isclose(exit_price - entry_price, fixed_profit), \
                'Should have a ${fixed_profit} diff between exit and entry prices'
            assert_exit_price_matches_exit_candle(uniform_df, trade)


def test_multiple_trades_fixed_take_profit_short_only(uniform_df):
    short_signals = np.zeros(len(uniform_df))
    short_signals[[0, 40, 50]] = 1
    assert len(np.where(short_signals==1)[0]) == 3, 'Should have 3 sell indices'
    config = deepcopy(fake_strat_config_manual(short_signals=short_signals))
    config['go_short'] = True
    for fixed_amount in [2, 2.1, 2.222, 2.123, 2.3456789, 3, 4, 5, 8, 9]:
        config['take_profit_value'] = fixed_amount
        config['take_profit_type'] = 'fixed' # 'fixed' or 'percent
        bt = compute_backtest_results(uniform_df, config)
        assert_bt_state(bt, e_dd = 0, e_max_drawdown = 0, e_n_trades = 3, e_n_wins = 3, 
            e_n_losses = 0, e_n_longs = 0, e_n_shorts = 3, e_length = len(uniform_df))
        for trade in bt.trades:
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            exit_candle = uniform_df.iloc[trade['end_index']]
            assert isclose(entry_price - exit_price, fixed_amount), \
                'Should have a ${fixed_amount} diff between exit and entry prices'
            assert_exit_price_matches_exit_candle(uniform_df, trade)
