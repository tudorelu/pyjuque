import math 
import json
import numpy as np

class BaseBacktester():
    def __init__(self, params = {}, strategies_dir='pyjuque.Strategies'):
        self.params = params
        # ENTRY SETTINGS
        for elem in ['entry_settings', 'exit_settings', 'strategy']:
            assert elem in list(params.keys()), 'Key {} should be inside the params dict! '.format(elem)
        self.initial_balance = 0
        if params.__contains__('starting_balance'):
            self.initial_balance = params['starting_balance']
        self.leverage = 1
        if params['entry_settings'].__contains__('leverage'):
            self.leverage = params['entry_settings']['leverage']
        self.fee = 0
        if params['entry_settings'].__contains__('fee'):
            self.fee = params['entry_settings']['fee']
        self.slippage = 0   # NOT USED YET
        if params['entry_settings'].__contains__('slippage'):
            self.slippage = params['entry_settings']['slippage']
        # GOLONG
        self.go_long = True
        if params['entry_settings'].__contains__('go_long'):
            self.go_long = params['entry_settings']['go_long']
        # GOSHORT
        self.go_short = False
        if params['entry_settings'].__contains__('go_short'):
            self.go_short = params['entry_settings']['go_short']
        self.reinvest_profits = False
        if params['entry_settings'].__contains__('reinvest_profits'):
            self.reinvest_profits = params['entry_settings']['reinvest_profits']
        self.ignore_last_candle = True
        if params['entry_settings'].__contains__('ignore_last_candle'):
            self.ignore_last_candle = params['entry_settings']['ignore_last_candle']

        self.trade_amount = None
        if params['entry_settings'].__contains__('trade_amount'):
            self.trade_amount = params['entry_settings']['trade_amount']
        self.use_base_amount = False
        if params['entry_settings'].__contains__('use_base_amount'):
            self.use_base_amount = params['entry_settings']['use_base_amount']
        self.initial_entry_allocation = 100
        if params['entry_settings'].__contains__('initial_entry_allocation'):
            self.initial_entry_allocation = params['entry_settings']['initial_entry_allocation']

        self.symbol = None
        if params.__contains__('symbol'):
            self.symbol = params['symbol']
        self.timeframe = None
        if params.__contains__('timeframe'):
            self.timeframe = params['timeframe']
        self.take_profit_value = math.inf
        if params['exit_settings'].__contains__('take_profit'):
            self.take_profit_value = (100 + params['exit_settings']['take_profit']) / 100
        self.stop_loss_value = 0
        if params['exit_settings'].__contains__('stop_loss_value'):
            self.stop_loss_value = (100 - params['exit_settings']['stop_loss_value']) / 100
        self.trailing_stop_loss = False
        if params['exit_settings'].__contains__('trailing_stop_loss'):
            self.trailing_stop_loss = params['exit_settings']['trailing_stop_loss']
        self.exit_on_short = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_short = params['exit_settings']['exit_on_signal']
        self.exit_on_long = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_long = params['exit_settings']['exit_on_signal']
        self.strategies_dir = strategies_dir
        self.strategy = self._init_strategy(params)
        # remembers the amount of fees paid so far for the open position
        self.balance = self.initial_balance
        self.n_longs = 0
        self.n_shorts = 0
        # amount that goes in a trade ?
        if self.trade_amount == None:
            self.trade_amount = self.initial_balance \
                * (self.initial_entry_allocation / 100) \
                * self.leverage
        self.fee_cost = self.fee / 100
        self.pnl_curve = []
        self.drawdown_curve = []
        self.equity_curve = []
        self.buyhold_curve = []
        self.position_curve = []
        self.trades = []
        self.max_drawdown = 0.
        self.gross_profit = 0.
        self.gross_loss = 0.
        self.max_flat_period = 0
        self.max_equity = self.balance
        self.winrate = 0.
        self.profit_factor = 0.
        self.total_fees_paid = 0.
        self.avg_trade_profit = 0.

    def _init_strategy(self, params):
        assert 'strategy' in list(params.keys()), "Key 'strategy' should be inside the params dict!"
        # STRATEGY
        if type(params['strategy']['class']) == str:
            self.strategy_name = params['strategy']['class']
            if type(params['strategy']['params']) == str:
                strategy_params = json.loads(params['strategy']['params'])
            else:
                strategy_params = params['strategy']['params']
            self.strategy_params = strategy_params
            strat_mod = __import__(self.strategies_dir + '.' + self.strategy_name, fromlist=[self.strategy_name])
            self.strategy_class = getattr(strat_mod, self.strategy_name) 
            strategy = self.strategy_class(**self.strategy_params)
        else:
            self.strategy_class = params['strategy']['class']
            self.strategy_name = self.strategy_class.__name__
            self.strategy_params = params['strategy']['params']
            strategy = self.strategy_class(**self.strategy_params)
        return strategy
    
    def _init_exit_settings(self, params):
        assert 'exit_settings' in list(params.keys()), "Key 'exit_settings' should be inside the params dict!"
        # EXIT SETTINGS
        self.take_profit_value = math.inf
        if params['exit_settings'].__contains__('take_profit'):
            self.take_profit_value = (100 + params['exit_settings']['take_profit']) / 100
        self.stop_loss_value = 0
        if params['exit_settings'].__contains__('stop_loss_value'):
            self.stop_loss_value = (100 - params['exit_settings']['stop_loss_value']) / 100
        self.trailing_stop_loss = False
        if params['exit_settings'].__contains__('trailing_stop_loss'):
            self.trailing_stop_loss = params['exit_settings']['trailing_stop_loss']
        self.exit_on_short = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_short = params['exit_settings']['exit_on_signal']
        self.exit_on_long = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_long = params['exit_settings']['exit_on_signal']
        self.sell_on_end = False
        if params['exit_settings'].__contains__('sell_on_end'):
            self.sell_on_end = params['exit_settings']['sell_on_end']
        self.sell_on_end = False
        if params['exit_settings'].__contains__('sell_on_end'):
            self.sell_on_end = params['exit_settings']['sell_on_end']

    def _strategy_to_position(self):
        """ Given a strategy, it returns a position array. """
        position = []
        pos = 0
        # Convert signals lists to ndarrays if they are not already
        if type(self.strategy.long_signals) != np.ndarray \
            or type(self.strategy.short_signals) != np.ndarray:
            self.strategy.long_signals = np.array(self.strategy.long_signals)
            self.strategy.short_signals = np.array(self.strategy.short_signals)
        s = self.strategy.long_signals - self.strategy.short_signals
        for s_i in s.tolist():
            if s_i != 0:
                pos = s_i
            position.append(pos)
        position = np.asarray(position)
        if self.go_long and self.go_short:
            pass
        elif self.go_long:
            position = np.where(position==1, 1, 0)
        elif self.go_short:
            position = np.where(position==-1, -1, 0)
        return position

    def _get_close(self, data):
        if 'close' in data.columns:
            close = np.asarray(data['close'])
        elif 'price' in data.columns:
            close = np.asarray(data['price'])
        else:
            raise ValueError('Dataframe does not contain "close" nor "price" columns')
        return close

    def _get_returns(self, close=None, data=None):
        if close == None and data == None:
            raise ValueError('Either one of "close" or "data" should be not empty.')
        if close == None:
            close = self._get_close(data)
        # Compute or get returns
        if 'returns' not in data.columns:
            returns = np.log(close / np_shift(close, 1))
        else:
            returns = np.asarray(data['returns'])
        # Compute or get cummuative returns
        if 'creturns' not in data.columns:
            creturns = np.exp(np.cumsum(returns))
        else:
            creturns = np.asarray(data['creturns'])
        return returns, creturns
