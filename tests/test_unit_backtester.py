
from pprint import pprint
from copy import deepcopy
from math import isclose
from .utils import (df, long_signals_np, short_signals_np, fake_strat_config, 
    long_signal_indices, short_signal_indices, MomentumStrategy, uniform_df,
    fake_strat_config_manual, assert_exit_price_matches_exit_candle)
from pyjuque.Backtester import Backtester
from pytest import raises
import numpy as np
# from pyjuque.backtester.Exceptions import InvalidBacktesterConfigError

config_dict = dict(
        strategy_class = MomentumStrategy,
        trade_amount = 10,
        fee_percent = 0.1,
        go_long = True,
        go_short = False,
        exit_on_short = True
    )


def test_init_config_should_pass():
    config = dict(
        strategy_class = MomentumStrategy,
        go_long = True,
        exit_on_short = True)
    Backtester(config = config)
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        trade_amount = 100,
        go_long = True,
        exit_on_short = True))
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        trade_amount = 0.01,
        go_long = True,
        exit_on_short = True))
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        go_short = True,
        exit_on_long = True,
        fee_percent = 1))
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        go_short = True,
        exit_on_long=True))
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        strategy_params = dict(momentum_period=5),
        go_long = True,
        take_profit_value=1))
    Backtester(config = dict(
        strategy_class = MomentumStrategy,
        go_long = True,
        go_short = True))


def test_init_config_should_fail():
    with raises(TypeError):
        # Config must at least contain the strategy_class
        bt = Backtester({})

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            trade_amount = None,
            go_long = True,
            exit_on_short = True))

    with raises(TypeError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            trade_amount = '0.01',
            go_long = True,
            exit_on_short = True))

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            fee_percent = 101,
            go_long = True,
            exit_on_short = True))

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            fee_percent = -3,
            go_long = True,
            exit_on_short = True))

    with raises(TypeError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            go_short = 'False',
            go_long = True,
            exit_on_short = True))

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            strategy_params = dict(momentum_period=5),
            exit_on_short = False))

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            strategy_params = dict(momentum_period=5)))

    with raises(ValueError):
        Backtester(config = dict(
            strategy_class = MomentumStrategy,
            strategy_params = dict(momentum_period=5),
            go_long = True))


def test_strategy_to_position_array_just_long(df, fake_strat_config):
    config = deepcopy(fake_strat_config)
    config['go_long'] = True
    config['exit_on_short'] = True
    bt = Backtester(config=config)
    pos_array = bt._strategy_to_position_array()
    assert pos_array.shape == (len(df),), "Wrong shape"
    assert 0 in pos_array, "Should have a neutral position (0)"
    assert 1 in pos_array, "Should have a long position (1)"
    assert -1 not in pos_array, "Should not have a short position (-1)"


def test_strategy_to_position_array_long_short(df, fake_strat_config):
    config = deepcopy(fake_strat_config)
    config['go_long'] = True
    config['go_short'] = True
    bt = Backtester(config=config)
    pos_array = bt._strategy_to_position_array()
    assert pos_array.shape == (len(df),), "Wrong shape"
    assert 0 in pos_array, "Should have a neutral position (0)"
    assert 1 in pos_array, "Should have a long position (1)"
    assert -1 in pos_array, "Should have a short position (-1)"


def test_strategy_to_position_array_just_short(df, fake_strat_config):
    config = deepcopy(fake_strat_config)
    config['go_short'] = True
    config['exit_on_long'] = True
    bt = Backtester(config=config)
    pos_array = bt._strategy_to_position_array()
    assert pos_array.shape == (len(df),), "Wrong shape"
    assert 0 in pos_array, "Should have a neutral position (0)"
    assert 1 not in pos_array, "Should not have a long position (1)"
    assert -1 in pos_array, "Should have a short position (-1)"


def test_strategy_to_position_array_long_short_trade_indices(fake_strat_config):
    config = deepcopy(fake_strat_config)
    config['go_long'] = True
    config['go_short'] = True
    bt = Backtester(config=config)
    l_i = long_signal_indices()
    s_i = short_signal_indices()
    pos_arr = bt._strategy_to_position_array()
    for i in s_i:
        assert pos_arr[i] == -1, f"Should have a short position (-1) at index {i}"
    for i in l_i:
        assert pos_arr[i] == 1, f"Should have a long position (1) at index {i}"


def test_preprocess_data(df, fake_strat_config, long_signals_np, short_signals_np):
    config = deepcopy(fake_strat_config)
    config['go_long'] = True
    config['go_short'] = True
    bt = Backtester(config=config)
    bt._preprocess_data(df)
    long_trades = np.where(long_signals_np==1)[0]
    short_trades = np.where(short_signals_np==1)[0]
    all_possible_trades = np.concatenate((long_trades, short_trades))
    for i in bt.idx_trades: 
        assert i in all_possible_trades, f'Should have a trade at index {i}'



def test_tp_function_percent(df):
    long_signals = np.zeros(len(df))
    long_signals[10] = 1
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    for pct in [0, 0.1, 0.5, 1, 2, 3, 4, 5, 10, 13, 13.333, 55.55, 80]:
        config['take_profit_value'] = pct
        bt = Backtester(config=config)
        assert not bt._get_tp_price is None, '"_get_tp_price" function should not be None'
        assert bt._get_sl_price is None, '"_get_sl_price" function should be None'
        long_multiplier = (100 + pct) / 100
        short_multiplier = (100 - pct) / 100
        for price in range(1, 9999):
            price = price / 3
            assert isclose(bt._get_tp_price(price, 1), price * long_multiplier), \
                f'Should have a take profit price of {price * long_multiplier} at price {price}'
            assert isclose(bt._get_tp_price(price, -1), price  * short_multiplier), \
                f'Should have a take profit price of {price * short_multiplier} at price {price}'
        bt.backtest(df)
        res = bt.get_results()
        assert len(bt.pnl) == len(df), 'PNL length should be equal to df length'
        assert len(bt.drawdown) == len(df), 'DD length should be equal to df length'
        if bt.n_trades > 0:
            trade = bt.trades[0]
            target_exit = trade['entry_price'] * long_multiplier
            if trade['end_index'] < len(df) - 1:
                assert isclose(trade['exit_price'], target_exit), \
                    f'Trade exit price should be close to {target_exit} but is {trade["exit_price"]}'
            assert_exit_price_matches_exit_candle(df, trade)


def test_tp_function_fixed(df):
    long_signals = np.zeros(len(df))
    long_signals[10] = 1
    config = deepcopy(fake_strat_config_manual(long_signals=long_signals))
    config['go_long'] = True
    config['take_profit_type'] = 'fixed'
    for fixed in [0, 0.0014, 0.1, 0.5, 1, 2, 3, 4, 5, 10, 13, 13.333, 55.55, 80]:
        config['take_profit_value'] = fixed
        bt = Backtester(config=config)
        assert not bt._get_tp_price is None, '"_get_tp_price" function should not be None'
        assert bt._get_sl_price is None, '"_get_sl_price" function should be None'
        for price in range(1, 9999):
            price = price / 3
            target_long_price = price + fixed
            target_short_price = max(0, price - fixed) 
            assert isclose(bt._get_tp_price(price, 1), target_long_price), \
                f'Should have a take profit price of {target_long_price} at price {price}'
            assert isclose(bt._get_tp_price(price, -1), target_short_price), \
                f'Should have a take profit price of {target_short_price} at price {price}'
        bt.backtest(df)
        res = bt.get_results()
        assert len(bt.pnl) == len(df), 'PNL length should be equal to df length'
        assert len(bt.drawdown) == len(df), 'DD length should be equal to df length'
        if bt.n_trades > 0:
            trade = bt.trades[0]
            target_exit = trade['entry_price'] + fixed
            if trade['end_index'] < len(df) - 1:
                assert isclose(trade['exit_price'], target_exit), \
                    f'Trade exit price should be close to {target_exit} but is {trade["exit_price"]}'
            assert_exit_price_matches_exit_candle(df, trade)
