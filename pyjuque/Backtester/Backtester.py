"""
Written by Tudor Barbulescu 
hello(at)tudorbarbulescu.com

This class deals with backtesting.
"""

import numpy as np 
from time import time as timer
from pyjuque.Backtester.BaseBacktester import BaseBacktester
from pyjuque.Utils.Plotter import PlotData

"""
TODO:
Calculate extra stats - profit factor, gross profit, gross loss, sharpe ratio & others
"""
class Backtester(BaseBacktester):
    def __init__(self, params = {}, strategies_dir='pyjuque.Strategies'):
        super().__init__(params, strategies_dir)
        # remembers the amount of fees paid so far for the open position
        self.balance = self.initial_balance
        self.n_longs = 0
        self.n_shorts = 0
        # amount that goes in a trade ?
        # if self.trade_amount == None:
        #     self.trade_amount = self.initial_balance \
        #         * self.leverage \
        #         * (self.initial_entry_allocation / 100)
        self.fee_cost = self.fee / 100
        self.pnl_curve = []
        self.drawdown_curve = []
        self.equity_curve = []
        self.buyhold_curve = []
        self.position_curve = []
        # self.cummax_curve = []
        # self.cumstrat_curve = []
        self.trades = []
        self.max_drawdown = 0.
        # TODO: Calculate the following
        self.gross_profit = 0.
        self.gross_loss = 0.
        self.max_flat_period = 0.
        self.max_equity = self.balance
        self.winrate = 0.
        self.profit_factor = 0.
        self.total_fees_paid = 0.
        self.profit_avg_trade = 0.
        self.longest_drawdown_period = 0
        self.average_drawdown_period = 0
        self.sharpe_ratio = None

    def backtest(self, df, **strategy_kwargs):
        # setup strategy on given dataframe (computes signals)
        self.strategy.setUp(df=df, **strategy_kwargs)
        # extract position array from the strategy accross the given dataframe
        # 1 = long position, -1 = short, 0 = not holding
        self.position = self._strategy_to_position()
        # get the indices of all trades
        self.idx_trades = np.where(np.diff(self.position) != 0)[0] + 1
        # initialise other arrays and variables
        self.first_long = False                 # Was the first signal long or short?
        self.idx_longs = []                     # Holds indices of all long signals
        self.idx_shorts = []                    # Holds indices of all short signals
        self.n_longs = 0                        # Holds the number of all long signals
        self.n_shorts = 0                       # Holds the number of all short signals
        self.pnl = []                           # Holds the pnl value of every candle
        self.max_pnl = []                       # Holds the max_pnl value of every candle
        self.drawdown = []                      # Holds the drawdown value of every candle
        self.equity = []                        # Holds the EQUITY value of every candle
        self.total_trades = 0                   # Holds the total number of trades
        self.total_fees_paid = 0                # Holds the net amount of fees paid
        self.data = self.strategy.dataframe
        self.close = self._get_close(self.strategy.dataframe)
        l_d = len(self.data)
        l_t = len(self.idx_trades)
        # If we have at least one trade, compute the profits
        if l_t > 0:
            # Find if starting with long or short
            if self.position[self.idx_trades[0]] == 1:
                self.first_long = True
            elif self.position[self.idx_trades[0]] == -1:
                self.first_long = False
            else:
                raise ValueError('idx_first_trade should be 1 or -1,' \
                    f' but is {self.position[self.idx_trades[0]]}!')
            # Compute the pnl curve & trade by trade info
            trade_id = 0
            trades = []
            pnl_curve = np.zeros(self.idx_trades[0])
            prev_pnl = 0.
            prev_long = False
            # iterate through trade indices and build pnl curve section by section 
            for i in range(l_t):
                # get the start and end indices of this section
                idx_st = self.idx_trades[i]
                if i == l_t - 1:
                    idx_end = l_d
                else:
                    idx_end = self.idx_trades[i+1]
                # compute pnl_curve section for this trade
                made_trade = False
                if self.position[idx_st] == 1:
                    section_pnl = (self.close[idx_st:idx_end+1] / self.close[idx_st]) - 1 - self.fee_cost
                    section_pnl[-1] = section_pnl[-1] - self.fee_cost
                    self.n_longs += 1
                    made_trade = True
                    prev_long = True
                    self.idx_longs.append(idx_st)
                elif self.position[idx_st] == -1:
                    section_pnl = (self.close[idx_st] / self.close[idx_st:idx_end+1]) - 1 - self.fee_cost
                    section_pnl[-1] = section_pnl[-1] - self.fee_cost
                    self.n_shorts += 1
                    made_trade = True
                    prev_long = False
                    self.idx_shorts.append(idx_st)
                elif self.position[idx_st] == 0:
                    section_pnl = [0] * (idx_end - idx_st - 1)
                    if prev_long:
                        self.idx_shorts.append(idx_st)
                    else:
                        self.idx_longs.append(idx_st)
                else:
                    raise ValueError(f"Getting position value " \
                        f"{self.position[idx_st]}: other than -1, 0, 1!")
                # add trade to trades list
                if made_trade:
                    trade_id += 1
                    trades.append(dict(id = trade_id, pnl = section_pnl, is_long = prev_long))
                # make trade part of entire pnl curve
                section_pnl = prev_pnl + section_pnl
                pnl_curve = np.concatenate((pnl_curve, section_pnl))
                prev_pnl = pnl_curve[-1]
        else:
            pnl_curve = np.zeros(l_d)
        ########
        self.pnl = pnl_curve
        # Here we compute drawdown and equity curves
        ret = 1 + self.pnl
        self.drawdown = (ret / np.maximum.accumulate(ret)) - 1
        self.max_drawdown = round(-np.amin(self.drawdown), 2)
        dd_periods = np.diff(np.where(self.drawdown == 0)[0])
        if len(dd_periods) > 0:
            self.longest_drawdown_period = np.amax(dd_periods)
            self.average_drawdown_period = np.average(dd_periods)
        self.equity = self.pnl * self.trade_amount
        self.max_equity = round(np.amax(self.equity), 2)
        self.total_trades = self.n_longs + self.n_shorts
        self.total_fees_paid = self.total_trades * 2 * self.fee_cost * self.trade_amount

    def compute_plotting_signals(self):
        """ Called after running backtest, we compute all the plotting info. """
        times = self.data.time.values
        closes = self.data.close.values
        opens = self.data.open.values
        l_d = len(self.data) 
        self.longs = [(times[i], closes[i], 15) for i in self.idx_longs]
        self.shorts = [(times[i],closes[i], 15) for i in self.idx_shorts]
        self.pnl_curve = [(times[i], self.pnl[i]) for i in range(l_d)]
        self.equity_curve = [(times[i], self.equity[i]) for i in range(l_d)]
        self.drawdown_curve = [(times[i], self.drawdown[i]) for i in range(l_d)]
        # self.max_pnl_curve = [(times[i], self.max_pnl[i]) for i in range(l_d)]

    def get_fig(self, extra_indicators=None, **kwargs):
        """ """
        self.compute_plotting_signals()
        plot_indicators=[
            dict(title = 'equity', source = self.equity_curve, yaxis='y2', 
                                    fill='tozeroy', color='green'),
            dict(title = 'drawdown', source = self.drawdown_curve, yaxis='y3', 
                                    fill='tozeroy', color='indianred'),
        ] 
        if extra_indicators != None:
            for ind in extra_indicators:
                plot_indicators.append(dict(title = ind['name'], 
                                    name = ind['name'], yaxis=ind['yaxis']))
        fig = PlotData(self.data, **kwargs,
            signals=[
                dict(name = 'entry orders', points = self.longs, 
                    marker_symbol='triangle-up', marker_color='green'), 
                dict(name = 'exit orders', points = self.shorts, 
                    marker_symbol='triangle-down', marker_color='red'),
            ],
            plot_indicators = plot_indicators,
        )
        fig.update_layout(autosize=True)
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        return fig

    def return_results(self):
        """ Returns a dict with the backtesting results """
        if self.total_trades > 0:
            self.profit_avg_trade = self.equity[-1] / self.total_trades
        l_d = len(self.data)
        pnl_ratio = 0
        equity = 0
        if(len(self.pnl) > 0):
            pnl_ratio = self.pnl[-1]
            equity = self.equity[-1]
        results = {
            'start_time' : self.data.time.iloc[0],
            'end_time' : self.data.time.iloc[-1],
            'strategy_name' : self.strategy_name,
            'strategy_params' : self.strategy_params,
            'trade_amount' : self.trade_amount,
            'profit_net' : equity,
            'total_fees_paid': self.total_fees_paid,
            # 'profit_factor' :  self.profit_factor, 
            # 'gross_profit': self.gross_profit,
            # 'gross_loss': self.gross_loss,
            'pnl_ratio': pnl_ratio,
            # 'profit_avg_trade': self.profit_avg_trade,
            # 'profit_net_longs': self.profit_net_longs,
            # 'profit_net_shorts': self.profit_net_shorts,
            'max_drawdown': self.max_drawdown,
            'max_equity': self.max_equity,
            'longest_drawdown_period': float(self.longest_drawdown_period / l_d),
            'average_drawdown_period': int(self.average_drawdown_period),
            # 'max_flat_period' : self.max_flat_period,
            # 'timeframe' : self.timeframe,
            # 'symbol': self.symbol,
            'n_longs' : self.n_longs,
            'n_shorts': self.n_shorts,
            'n_total_trades' : self.total_trades,
            # 'n_winning_trades': self.n_winning_trades,
            # 'n_losing_trades' : self.n_losing_trades,
            # 'winrate' : self.winrate,
        }
        return results
