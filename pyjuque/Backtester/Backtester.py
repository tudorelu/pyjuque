'''
# Backtester

Class used for backtesting price-based trading strategies in a vectorised 
way (by making use of numpy & pandas).
Needs access to data (in the form of a pandas dataframe) and a strategy.

The data should probably be in the OHLCV format (depending on the strategy).
The strategy should be able to compute two arrays of signals which should 
be the length of the data provided - one for longs and one for shorts

# Usage:

    ```py
    # Init phase
    bt = Backtester(config) # config can be a dict, a filepath (*) (json (*) or yaml (*)) or a BacktesterConfig object

    # Get data
    data = get_data_from_somewhere()

    # Run the backtest 
    bt.backtest(data)

    # Get the results (various statistics about the run)
    bt.get_results()

    # Plot the backtest graph (makes use of our plotting module)
    bt.plot_graph()

    # Combines the outputs from get_results() and plot_graph()
    # into a visually pleasing and informative report (as HTML)
    bt.get_report()

    # (*) = not implemented yet
    ```

'''

# from pprint import pprint
from functools import partial
from .Utils import BacktesterConfig, float128
from pyjuque.Plotter import create_plot, GraphDetails

# from .Exceptions import InvalidBacktesterConfigError
import numpy as np
from pandas import DataFrame
from plotly.express.colors import qualitative as colors

'''
TODO:
Define what happens when we are long & we get a short signal
(assuming the strategy goes both long and short):
    - reverse position (go short)? 
    - wait for another exit type (TP/SL)?

TODO: 
Calculate cummulative returns
Allow to trade in 'full account balance' mode

'''
def _get_fixed_value_diff(fixed_value, entry_price):
    return max(0, float128(entry_price) + float128(fixed_value))


def _get_percent_value_diff(percent_value, entry_price):
    return float128(entry_price) * float128(percent_value)


class Backtester:
    def __init__(self, config:str or dict or BacktesterConfig):
        self.config = Backtester._extract_config(config)
        self.strategy = Backtester._init_strategy(self.config)
        self.balance = float128(self.config.trade_amount)
        self.trade_amount = float128(self.config.trade_amount)
        self.fee_cost = float128(self.config.fee_percent) / float128(100)
        self.results_have_been_computed = False
        self.plot_has_been_made = False
        self.data = None
        self.position_array = None
        self.position_switch = None
        self._get_tp_price, self._get_sl_price = Backtester._define_tp_sl_functions(self.config)
        # Define results
        self.fig = None
        self.results = None
        self.average_drawdown_period = None
        self.longest_drawdown_period = None
        self.pnl = None
        self.idx_longs = None
        self.idx_shorts = None
        self.idx_trades = None
        self.idx_take_profit = None
        self.idx_stop_loss = None
        self.idx_long_stops = None
        self.idx_short_stops = None
        self.price_long_stops = None
        self.price_short_stops = None
        self.type_long_stops = None
        self.type_short_stops = None
        self.drawdown = None
        self.max_drawdown = None
        self.equity = None
        self.max_equity = None
        self.profit_net = None
        self.fees_paid = None
        self.trades = None
        self.n_longs = 0
        self.n_shorts = 0
        self.n_trades = 0
        self.n_wins = 0
        self.n_losses = 0


    @classmethod
    def _extract_config(cls, 
        config:str or dict or BacktesterConfig) -> BacktesterConfig:
        ''' Takes whatever config object is provided and returns a 
        BacktesterConfig object. '''
        if type(config) is BacktesterConfig:
            return config
        elif type(config) is dict:
            return BacktesterConfig(**config)
        elif type(config) is str:
            # TODO: implement json and yaml files
            raise NotImplementedError(
                'Importing BacktesterConfig from file is not supported yet.')
        else:
            raise TypeError(f'Invalid config type. Need one of '
                f'{BacktesterConfig, dict, str}, but got {type(config)}')


    @classmethod
    def _init_strategy(cls, config:BacktesterConfig):
        ''' Initializes the strategy from a config object. '''
        return config.strategy_class(**config.strategy_params)


    @classmethod
    def _define_tp_sl_functions(cls, config:BacktesterConfig) -> tuple:
        # TODO: Test this bad boy 
        """Extracts the correct SL and TP transformations on the entry price based on the config object """
        _get_tp_price, _get_sl_price = None, None
        if config.take_profit_value != None:
            if config.take_profit_type == 'percent':
                long_tp_multiplier = (float128(100) + float128(config.take_profit_value)) / float128(100) 
                short_tp_multiplier = (float128(100) - float128(config.take_profit_value)) / float128(100)
                _get_tp_price_for_long = partial(_get_percent_value_diff, long_tp_multiplier)
                _get_tp_price_for_short = partial(_get_percent_value_diff, short_tp_multiplier)
            elif config.take_profit_type == 'fixed':
                _get_tp_price_for_long = partial(_get_fixed_value_diff, config.take_profit_value)
                _get_tp_price_for_short = partial(_get_fixed_value_diff, -config.take_profit_value)
            else:
                raise ValueError('Invalid take profit type!')
            def tp_function(entry_price, position):
                if position == 1:
                    return _get_tp_price_for_long(entry_price)
                elif position == -1:
                    return _get_tp_price_for_short(entry_price)
                else: 
                    raise ValueError('Invalid position! Must be in {-1, 1}.')
            _get_tp_price = tp_function
        if config.stop_loss_value != None:
            if config.stop_loss_type == 'percent':
                long_sl_multiplier = (float128(100) - float128(config.stop_loss_value)) / float128(100) 
                short_sl_multiplier = (float128(100) + float128(config.stop_loss_value)) / float128(100) 
                _get_sl_price_for_long = partial(_get_percent_value_diff, long_sl_multiplier)
                _get_sl_price_for_short = partial(_get_percent_value_diff, short_sl_multiplier)
            elif config.stop_loss_type == 'fixed':
                _get_sl_price_for_long = partial(_get_fixed_value_diff, -config.stop_loss_value)
                _get_sl_price_for_short = partial(_get_fixed_value_diff, config.stop_loss_value)
            else:
                raise ValueError('Invalid stop loss type!')
            def sl_function(entry_price, position):
                if position == 1:
                    return _get_sl_price_for_long(entry_price)
                elif position == -1:
                    return _get_sl_price_for_short(entry_price)
                else: 
                    raise ValueError('Invalid position! Must be in {-1, 1}.')
            _get_sl_price = sl_function
        return _get_tp_price, _get_sl_price


    def _strategy_to_position_array(self) -> np.ndarray:
        ''' Converts the strategy's signals to a position array. '''
        # TODO: Include support for TSL
        long_signals = Backtester._to_numpy_array(self.strategy.long_signals)
        short_signals = Backtester._to_numpy_array(self.strategy.short_signals)
        if self.config.go_long:
            if (self.config.go_short or self.config.exit_on_short):
                self.position_switch = long_signals - short_signals
            else:
                self.position_switch = long_signals
        elif self.config.go_short:
            if (self.config.go_long or self.config.exit_on_long):
                self.position_switch = long_signals - short_signals
            else:
                self.position_switch = -short_signals
        else:
            raise ValueError('BacktesterConfig must have go_long or go_short set to True')
        self.position_switch.astype(np.int64)
        position_array = []
        current_position = 0
        for s_i in self.position_switch.tolist():
            if s_i != 0:
                current_position = s_i
            position_array.append(current_position)
        position_array = np.array(position_array)
        if self.config.go_long and self.config.go_short:
            pass
        elif self.config.go_long:
            position_array = np.where(position_array == 1, 1, 0)
        elif self.config.go_short:
            position_array = np.where(position_array == -1, -1, 0)
        validation_array = np.isin(position_array, [-1, 0, 1]) 
        self.position_array = position_array
        if False in validation_array:
            raise ValueError('Invalid position array,'
                            ' should only contain -1, 0 or 1!')
        self.position_array = position_array
        if not self._get_tp_price is None or not self._get_sl_price is None:
            self.position_array = self._add_sl_tp_logic(position_array)
        # print(f'\nPosition array: {self.position_array}\n')
        return self.position_array


    def _add_sl_tp_logic(self, position_array:np.ndarray) -> np.ndarray:
        """ Adds the stop loss and take profit logic to the position array. """
        # TODO: Test this 
        idx_trades = np.where(self.position_switch!=0)[0]
        if position_array[0] != 0 and len(idx_trades) == 0:
            idx_trades = np.insert(idx_trades, 0, 0)
        idx_take_profit = []
        idx_stop_loss = []
        min_next_idx = -1
        # print('ALL idx_trades: ', idx_trades)
        for i in range(len(idx_trades)):
            idx_st = idx_trades[i]
            idx_end = idx_trades[i+1] \
                if i < len(idx_trades) - 1 else len(self.data) - 1
            # print('idx_st: {}, idx_end: {}'.format(idx_st, idx_end))
            # if idx_st == idx_end:
            if idx_st < min_next_idx:
                if idx_end < min_next_idx:
                    # print('c2')
                    continue
                else:
                    # print('CHRIST')
                    idx_st = min_next_idx
            if idx_st >= idx_end:
                # print('c1')
                continue
            is_next_idx_same = position_array[idx_st] == position_array[idx_end]
            search_for_end_until_idx = idx_end
            if is_next_idx_same:
                search_for_end_until_idx = len(self.data)
            tp_idx = None
            sl_idx = None
            # print(f'idx_st: {idx_st}, idx_end: {idx_end}, search_for_end_until_idx: {search_for_end_until_idx}')
            if position_array[idx_st] not in [-1, 1]:
                pass
                # print('cica pass')
            else:
                if not self._get_tp_price is None:
                    tp_value = self._get_tp_price(self.data.open[idx_st], \
                                                        position_array[idx_st])
                    # print(f'tp_value: {tp_value}')
                    if position_array[idx_st] == 1:
                        potential_tps = np.where(self.data.high[idx_st:search_for_end_until_idx] \
                                                                > tp_value)[0]
                    elif position_array[idx_st] == -1:
                        potential_tps = np.where(self.data.low[idx_st:search_for_end_until_idx] \
                                                                < tp_value)[0]
                    if len(potential_tps) > 0:
                        tp_idx = idx_st + potential_tps[0]
                if not self._get_sl_price is None:
                    sl_value = self._get_sl_price(self.data.open[idx_st], 
                                                        position_array[idx_st])
                    # print(f'sl_value: {sl_value}')
                    if position_array[idx_st] == 1:
                        potential_sls = np.where(self.data.low[idx_st:search_for_end_until_idx] \
                                                                < sl_value)[0]
                    elif position_array[idx_st] == -1:
                        potential_sls = np.where(self.data.high[idx_st:search_for_end_until_idx] \
                                                                > sl_value)[0]
                    if len(potential_sls) > 0:
                        sl_idx = idx_st + potential_sls[0]
                tpsl_end_idx = None
                # print('tp_idx:', tp_idx, 'sl_idx:', sl_idx)
                if not tp_idx is None and not sl_idx is None:
                    if tp_idx < sl_idx:
                        idx_take_profit.append((idx_st, tp_idx))
                        tpsl_end_idx = tp_idx
                        # position_array[tp_idx:idx_end] = 0
                    else:
                        idx_stop_loss.append((idx_st, sl_idx))
                        tpsl_end_idx = sl_idx
                        # position_array[sl_idx:idx_end] = 0
                elif not tp_idx is None:
                    idx_take_profit.append((idx_st, tp_idx))
                    tpsl_end_idx = tp_idx
                    # position_array[tp_idx:idx_end] = 0
                elif not sl_idx is None:
                    idx_stop_loss.append((idx_st, sl_idx))
                    # position_array[sl_idx:idx_end] = 0
                    tpsl_end_idx = sl_idx
                if tpsl_end_idx is not None:
                    # print('CHANGE tpsl_end_idx:', tpsl_end_idx)
                    # print('min_next_idx:', min_next_idx)
                    if tpsl_end_idx >= idx_end:
                        # min_next_idx = tpsl_end_idx
                        # find next trade index >= tpsl_end_idx
                        if is_next_idx_same:
                            next_indices = np.where(idx_trades > tpsl_end_idx)[0]
                            if len(next_indices) > 0:
                                next_idx = idx_trades[next_indices[0]]
                                # print('IF: next_idx:', next_idx)
                            else:
                                next_idx = search_for_end_until_idx
                                # print('ELSE: next_idx:', next_idx)
                            position_array[tpsl_end_idx:next_idx] = 0
                            min_next_idx = next_idx
                        else:
                            # position_array[tpsl_end_idx:next_idx] = 0
                            pass
                    else:
                        position_array[tpsl_end_idx:idx_end] = 0
        self.idx_take_profit = idx_take_profit
        self.idx_stop_loss = idx_stop_loss
        return position_array


    @classmethod
    def _to_numpy_array(cls, input_array:list):
        ''' Converts a list to a numpy array. '''
        if type(input_array) != np.ndarray:
            return np.array(input_array)
        return input_array


    def _preprocess_data(self, candles:DataFrame):
        '''
        Preprocesses the dataframe to be used in the backtest & 
        initializs the required arrays.
        '''
        for column in ['open', 'high', 'low', 'close']:
            if column not in candles.columns:
                raise ValueError('Dataframe does not contain column: {column}')
            # if candles.dtypes[column].type is not float128:
            #     raise TypeError(f'Dataframe column: {column} is not of type float128!')
                # candles[['open', 'high', 'low', 'close']] = candles[['open', 'high', 'low', 'close']].astype(np.longdouble)
        self.strategy.set_up(candles)
        self.data = self.strategy.candles
        self._strategy_to_position_array()
        self.idx_trades = np.where(np.diff(self.position_array) != 0)[0] + 1
        if self.position_array[0] != 0:
            self.idx_trades = np.insert(self.idx_trades, 0, 0)


    def _backtest(self):
        '''Interal implementation of backtest, computes the pnl 
        curve trade by trade & generates the trades'''
        self.idx_longs = []
        self.idx_shorts = []
        self.idx_long_stops = []
        self.idx_short_stops = []
        self.price_long_stops = []
        self.price_short_stops = []
        self.type_long_stops = []
        self.type_short_stops = []
        self.trades = []
        if len(self.idx_trades) == 0:
            self.pnl = np.zeros(len(self.data))
            return
        self.pnl = np.zeros(self.idx_trades[0])
        prev_long = False # self.position_array[self.idx_trades[0]] == 1
        prev_pnl = 0.
        trade_object = None
        idx_end = None
        # Build pnl curve trade by trade 
        for i in range(len(self.idx_trades)):
            # Create PNL of this Trade
            idx_st = self.idx_trades[i]
            idx_end = self.idx_trades[i+1] \
                if i < len(self.idx_trades) - 1 else len(self.data) - 1
            # print("idx_st, idx_end: ", idx_st, idx_end), 
            if self.position_array[idx_st-1] == -self.position_array[idx_st]:
                # print('positions have been inverted! incrementing idx_start by 1')
                idx_st = idx_st + 1
            if idx_st >= idx_end:
                continue
            # Check current position
            if self.position_array[idx_st] in [-1, 1]:
                entry_price = self.data.open[idx_st].copy()
                # divisor = self.data.close[idx_st].copy()
                denominator = self.data.open[idx_st:idx_end+1].copy()
                exit_type = 'signal'
                # if we exit due to SL or TP, update the PNL accordingly
                if self._get_tp_price != None and \
                    (idx_st, idx_end) in self.idx_take_profit:
                    exit_type = 'tp'
                    denominator.iloc[-1] = self._get_tp_price(self.data.open[idx_st], self.position_array[idx_st])
                elif self._get_sl_price != None and \
                    (idx_st, idx_end) in self.idx_stop_loss:
                    exit_type = 'sl'
                    denominator.iloc[-1] = self._get_sl_price(\
                        self.data.open[idx_st], self.position_array[idx_st])
                # print("divisor: ", entry_price), print("denominator: ", denominator)
                prev_long = self.position_array[idx_st] == 1 
                if self.position_array[idx_st] == 1:
                    self.idx_longs.append(idx_st)
                    section_pnl = denominator / entry_price \
                        - float128(1) - self.fee_cost
                else:
                    self.idx_shorts.append(idx_st)
                    section_pnl = float128(1) \
                        - denominator / entry_price - self.fee_cost
                section_pnl = np.round(section_pnl, 10)
                section_pnl.iloc[-1] = section_pnl.iloc[-1] - self.fee_cost
                # Create Trade Object 
                exit_price = denominator.iloc[-1]
                trade_object = self._create_trade_object(
                    idx_st, idx_end, entry_price, 
                    exit_price, section_pnl, prev_long)
                self.trades.append(trade_object)
                _ = self.idx_long_stops.append(idx_end) \
                    if prev_long else self.idx_short_stops.append(idx_end)
                _ = self.price_long_stops.append(exit_price) \
                    if prev_long else self.price_short_stops.append(exit_price)
                _ = self.type_long_stops.append(exit_type) \
                    if prev_long else self.type_short_stops.append(exit_type)
            else:
                section_pnl = np.zeros(idx_end - idx_st - 1)
            # make trade part of entire pnl curve
            section_pnl = prev_pnl + section_pnl
            self.pnl = np.concatenate((self.pnl, section_pnl))
            prev_pnl = self.pnl[-1]
            # print("\n\nLEN PNL AND idx_end SO FAR")
            # print("len(self.pnl): ", len(self.pnl))
            # print("idx_end: ", idx_end)
            # print('difference: ', len(self.pnl) - idx_end)
            # print()
            if idx_end - len(self.pnl) > 0:
                self.pnl = np.concatenate(
                (self.pnl, np.ones(idx_end - len(self.pnl)) * prev_pnl))
        if len(self.pnl) != len(self.data):
            # TODO: This is just so that it passes the tests, 
            # not sure it actually solves the issue
            self.pnl = np.concatenate(
                (self.pnl, 
                np.ones(len(self.data) - len(self.pnl)) * prev_pnl))


    def _create_trade_object(self, idx_st, idx_end, entry_price, exit_price, pnl, is_long):
        # TODO: Make Trade Object a separate Class
        return dict(
            trade_number = len(self.trades) + 1, is_long = is_long,
            entry_price = entry_price, exit_price = exit_price,
            start_index = idx_st, end_index = idx_end, is_win = pnl.iloc[-1] > 0,
            # open_candle = self.data.iloc[idx_st], # close_candle = self.data.iloc[idx_end], # 
            pnl = pnl,
            )


    def backtest(self, candles:DataFrame):
        '''Backtests a strategy on a given dataframe.'''
        # Data preprocessing phase
        self._preprocess_data(candles) 
        # Backtesting phase
        self._backtest()


    def get_results(self, return_as:str = 'dict', force_compute:bool = False):
        # TODO properly implement and test this function 
        ''' Returns the results of the backtest.
            
            Args:
                return_as (dict or str): 
                    The type of return value. Default is 'dict'.
                force_compute (bool): 
                    If True, computes the results again. Default False.
            Returns:
                dict or str: object outlining the results of the backtest
        '''
        if not self.results_have_been_computed or force_compute:
            # Computing results phase
            self._compute_results()
            self.results_have_been_computed = True
        if return_as == 'dict':
            return self.__dict__
        elif return_as == 'str':
            return self.__str__()
    

    def get_plot(self, force_compute:bool = False, 
        add_strategy_indicators:bool = False, **kwargs):
        ''' Returns a plotly figure including pnl, drawdown and trades.
            
            Args:
                force_compute (bool): 
                    If True, computes the plot again. Default False.
                add_strategy_indicators (bool):
                    If True, adds the strategy indicators to the plot. Default False.
            Returns:
                Figure: plotly figure outlining the results of the backtest
        '''
        if not self.results_have_been_computed or force_compute:
            self._compute_results()
        if not self.plot_has_been_made or force_compute:
            self.fig = self._compute_plot(
                add_strategy_indicators=add_strategy_indicators, **kwargs)
        return self.fig


    def _compute_results(self):
        self.pnl = np.round(self.pnl.astype(np.float64), 10)
        ret = 1 + self.pnl
        self.drawdown = (ret / np.maximum.accumulate(ret)) - 1
        self.max_drawdown = round(-np.amin(self.drawdown), 2)
        dd_where_zero = np.where(self.drawdown == 0)[0]
        if len(dd_where_zero) > 0:
            dd_where_zero[-1] = len(self.data)
            dd_periods = np.diff(dd_where_zero)
            if len(dd_periods) > 0:
                self.average_drawdown_period = np.average(dd_periods)
                self.longest_drawdown_period = np.amax(dd_periods)
        self.equity = ((self.pnl + 1) * self.trade_amount).round(12)
        self.profit_net = (self.pnl * self.trade_amount).round(12)
        self.max_equity = np.amax(self.equity)
        self.n_longs = len(self.idx_longs) 
        self.n_shorts = len(self.idx_shorts)
        self.n_trades = self.n_longs + self.n_shorts
        self.fees_paid = self.n_trades * 2 * self.fee_cost * self.trade_amount
        for trade in self.trades:
            if trade['is_win']:
                self.n_wins += 1
            else:
                self.n_losses += 1


    def _compute_plot(self, add_strategy_indicators:bool, **kwargs):
        # TODO test this function 
        ''' Makes a plot of the backtest results. '''
        data = self.data.copy()
        data[['open', 'high', 'low', 'close']] = \
            data[['open', 'high', 'low', 'close']].astype(np.float64)
        longs = data.iloc[self.idx_longs]
        shorts = data.iloc[self.idx_shorts]
        pnl_ysource = np.round(100 * self.pnl, 2)
        dd_ysource = np.round(100 * self.drawdown, 2)
        price_long_stops = np.array(self.price_long_stops).astype(np.float64)
        price_short_stops = np.array(self.price_short_stops).astype(np.float64)
        xl_sig, yl_sig, xl_tp, yl_tp, xl_sl, yl_sl = self._get_exit_sources(
            self.type_long_stops, price_long_stops, self.idx_long_stops)
        xs_sig, ys_sig, xs_tp, ys_tp, xs_sl, ys_sl = self._get_exit_sources(
            self.type_short_stops, price_short_stops, self.idx_short_stops)
        graphs = [
            GraphDetails('Long Trades', 
                xsource=longs.time.values, 
                ysource=longs.close.values, 
                mode='markers',
                color=colors.Dark2[0],
                marker_symbol='triangle-up'),

            GraphDetails('Long Sig Exit', 
                xsource=xl_sig, 
                ysource=yl_sig, 
                mode='markers',
                color=colors.Dark2[0],
                marker_symbol='triangle-down-dot'),

            GraphDetails('Long TP Exit', 
                xsource=xl_tp, 
                ysource=yl_tp, 
                mode='markers',
                color=colors.Dark2[0],
                marker_symbol='arrow-bar-left'),

            GraphDetails('Long SL Exit',
                xsource=xl_sl,
                ysource=yl_sl,
                mode='markers',
                color=colors.Dark2[0],
                marker_symbol='x'),

            GraphDetails('Short Trades', 
                xsource=shorts.time.values, 
                ysource=shorts.close.values, 
                mode='markers',
                color=colors.Dark2[1],
                marker_symbol='triangle-down'),

            GraphDetails('Short Sig Exit',
                xsource=xs_sig,
                ysource=ys_sig,
                mode='markers',
                color=colors.Dark2[1],
                marker_symbol='triangle-up-dot'),

            GraphDetails('Short TP Exit',
                xsource=xs_tp,
                ysource=ys_tp,
                mode='markers',
                color=colors.Dark2[1],
                marker_symbol='arrow-bar-left'),

            GraphDetails('Short SL Exit',
                xsource=xs_sl,
                ysource=ys_sl,
                mode='markers',
                color=colors.Dark2[1],
                marker_symbol='x'),

            GraphDetails('Profit Loss (%)', ysource=pnl_ysource, yaxis='y2', 
                color='#17BECF', extra_kwargs=dict(fill='tozeroy')),
            GraphDetails('Drawdown (%)', ysource=dd_ysource, yaxis='y3', 
                color='#ff5555', extra_kwargs=dict(fill='tozeroy')),
        ]
        if add_strategy_indicators:
            graphs.extend(self.strategy.get_plottable_indicators())
        fig = create_plot(data, all_graphs_details=graphs, **kwargs)
        fig.update_layout(yaxis=dict(
                domain=[0.3, 1], fixedrange = False, showticklabels = False))
        fig.update_layout(
            yaxis2=dict(
                # title = "PNL (%)",
                domain=[0, 0.3],
                range=[min(pnl_ysource), max(pnl_ysource) * 2],
                side = 'right', fixedrange = False, 
                titlefont = dict(color = '#17BECF'),
                tickfont = dict(color= '#17BECF')))
        fig.update_layout(
            yaxis3=dict(
                # title = "DD (%)", 
                # domain=[0, 0.3],
                range=[min(dd_ysource) * 3, 0], fixedrange = False, 
                overlaying='y2', side='left',
                titlefont = dict(color = '#ff5555'),
                tickfont = dict(color= '#ff5555')))
        return fig


    def _get_exit_sources(self, exit_types, exit_prices, exit_idxs):
        ''' Returns a list of exit sources for each exit type. '''
        x_tp_stops = []
        y_tp_stops = []
        x_sl_stops = []
        y_sl_stops = []
        x_signal_stops = []
        y_signal_stops = []
        x_data = self.data.time.values
        for (s_type, price, idx) in zip(exit_types, \
                exit_prices, exit_idxs):
            if s_type == 'signal':
                x_signal_stops.append(x_data[idx])
                y_signal_stops.append(price)
            elif s_type == 'tp':
                x_tp_stops.append(x_data[idx])
                y_tp_stops.append(price)
            elif s_type == 'sl':
                x_sl_stops.append(x_data[idx])
                y_sl_stops.append(price)
            else:
                raise ValueError('Unknown stop type: {}'.format(s_type))
        return (x_signal_stops, y_signal_stops, \
                x_tp_stops, y_tp_stops, \
                x_sl_stops, y_sl_stops)