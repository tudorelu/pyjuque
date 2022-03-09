"""
Written by Tudor Barbulescu 
hello(at)tudorbarbulescu.com

This class deals with backtesting.
"""

import numpy as np 
from time import time as timer
from .BaseBacktester import BaseBacktester
from pyjuque.Utils.Plotter import PlotData

"""
TODO:
Calculate extra stats - profit factor, gross profit, gross loss, sharpe ratio & others
"""
class VectorisedBacktester(BaseBacktester):
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

    def compute_results(self):
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
        self.compute_results()
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


"""

========================================================= BACKTESTING REPORT ==========================================================
| Pair     |   Buys |   Avg Profit % |   Cum Profit % |   Tot Profit BTC |   Tot Profit % | Avg Duration |  Wins Draws Loss   Win%  |
|:---------|-------:|---------------:|---------------:|-----------------:|---------------:|:-------------|-------------------------:|
| ADA/BTC  |     35 |          -0.11 |          -3.88 |      -0.00019428 |          -1.94 | 4:35:00      |    14     0    21   40.0 |
| ARK/BTC  |     11 |          -0.41 |          -4.52 |      -0.00022647 |          -2.26 | 2:03:00      |     3     0     8   27.3 |
| BTS/BTC  |     32 |           0.31 |           9.78 |       0.00048938 |           4.89 | 5:05:00      |    18     0    14   56.2 |
| DASH/BTC |     13 |          -0.08 |          -1.07 |      -0.00005343 |          -0.53 | 4:39:00      |     6     0     7   46.2 |
| ENG/BTC  |     18 |           1.36 |          24.54 |       0.00122807 |          12.27 | 2:50:00      |     8     0    10   44.4 |
| EOS/BTC  |     36 |           0.08 |           3.06 |       0.00015304 |           1.53 | 3:34:00      |    16     0    20   44.4 |
| ETC/BTC  |     26 |           0.37 |           9.51 |       0.00047576 |           4.75 | 6:14:00      |    11     0    15   42.3 |
| ETH/BTC  |     33 |           0.30 |           9.96 |       0.00049856 |           4.98 | 7:31:00      |    16     0    17   48.5 |
| IOTA/BTC |     32 |           0.03 |           1.09 |       0.00005444 |           0.54 | 3:12:00      |    14     0    18   43.8 |
| LSK/BTC  |     15 |           1.75 |          26.26 |       0.00131413 |          13.13 | 2:58:00      |     6     0     9   40.0 |
| LTC/BTC  |     32 |          -0.04 |          -1.38 |      -0.00006886 |          -0.69 | 4:49:00      |    11     0    21   34.4 |
| NANO/BTC |     17 |           1.26 |          21.39 |       0.00107058 |          10.70 | 1:55:00      |    10     0     7   58.5 |
| NEO/BTC  |     23 |           0.82 |          18.97 |       0.00094936 |           9.48 | 2:59:00      |    10     0    13   43.5 |
| REQ/BTC  |      9 |           1.17 |          10.54 |       0.00052734 |           5.27 | 3:47:00      |     4     0     5   44.4 |
| XLM/BTC  |     16 |           1.22 |          19.54 |       0.00097800 |           9.77 | 3:15:00      |     7     0     9   43.8 |
| XMR/BTC  |     23 |          -0.18 |          -4.13 |      -0.00020696 |          -2.07 | 5:30:00      |    12     0    11   52.2 |
| XRP/BTC  |     35 |           0.66 |          22.96 |       0.00114897 |          11.48 | 3:49:00      |    12     0    23   34.3 |
| ZEC/BTC  |     22 |          -0.46 |         -10.18 |      -0.00050971 |          -5.09 | 2:22:00      |     7     0    15   31.8 |
| TOTAL    |    429 |           0.36 |         152.41 |       0.00762792 |          76.20 | 4:12:00      |   186     0   243   43.4 |
========================================================= SELL REASON STATS ==========================================================
| Sell Reason        |   Sells |  Wins |  Draws |  Losses |
|:-------------------|--------:|------:|-------:|--------:|
| trailing_stop_loss |     205 |   150 |      0 |      55 |
| stop_loss          |     166 |     0 |      0 |     166 |
| sell_signal        |      56 |    36 |      0 |      20 |
| force_sell         |       2 |     0 |      0 |       2 |
====================================================== LEFT OPEN TRADES REPORT ======================================================
| Pair     |   Buys |   Avg Profit % |   Cum Profit % |   Tot Profit BTC |   Tot Profit % | Avg Duration   |  Win Draw Loss Win% |
|:---------|-------:|---------------:|---------------:|-----------------:|---------------:|:---------------|--------------------:|
| ADA/BTC  |      1 |           0.89 |           0.89 |       0.00004434 |           0.44 | 6:00:00        |    1    0    0  100 |
| LTC/BTC  |      1 |           0.68 |           0.68 |       0.00003421 |           0.34 | 2:00:00        |    1    0    0  100 |
| TOTAL    |      2 |           0.78 |           1.57 |       0.00007855 |           0.78 | 4:00:00        |    2    0    0  100 |
=============== SUMMARY METRICS ===============
| Metric                | Value               |
|-----------------------+---------------------|
| Backtesting from      | 2019-01-01 00:00:00 |
| Backtesting to        | 2019-05-01 00:00:00 |
| Max open trades       | 3                   |
|                       |                     |
| Total/Daily Avg Trades| 429 / 3.575         |
| Starting balance      | 0.01000000 BTC      |
| Final balance         | 0.01762792 BTC      |
| Absolute profit       | 0.00762792 BTC      |
| Total profit %        | 76.2%               |
| Trades per day        | 3.575               |
| Avg. stake amount     | 0.001      BTC      |
| Total trade volume    | 0.429      BTC      |
|                       |                     |
| Best Pair             | LSK/BTC 26.26%      |
| Worst Pair            | ZEC/BTC -10.18%     |
| Best Trade            | LSK/BTC 4.25%       |
| Worst Trade           | ZEC/BTC -10.25%     |
| Best day              | 0.00076 BTC         |
| Worst day             | -0.00036 BTC        |
| Days win/draw/lose    | 12 / 82 / 25        |
| Avg. Duration Winners | 4:23:00             |
| Avg. Duration Loser   | 6:55:00             |
| Rejected Buy signals  | 3089                |
|                       |                     |
| Min balance           | 0.00945123 BTC      |
| Max balance           | 0.01846651 BTC      |
| Drawdown (Account)    | 13.33%              |
| Drawdown              | 0.0015 BTC          |
| Drawdown high         | 0.0013 BTC          |
| Drawdown low          | -0.0002 BTC         |
| Drawdown Start        | 2019-02-15 14:10:00 |
| Drawdown End          | 2019-04-11 18:15:00 |
| Market change         | -5.88%              |
===============================================


"""