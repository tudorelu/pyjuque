import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pyjuque.Plotting.Plotter import PlotData
from pyjuque.Exchanges.Binance import Binance
from pyjuque.Strategies.BaseStrategy import Strategy
from examples.pinescript_indicators import rsx_momentum_exhaustion

class CustomIndicatorStrategy(Strategy):

    def __init__(self, 
        mfi_length=14, 
        ob_level=70, 
        os_level=30):
        # Minimum period needed for indicators to be calculated
        self.minimum_period = 100
        self.mfi_length = mfi_length 
        self.ob_level = ob_level
        self.os_level = os_level
        self.indicators = [
            dict(
                indicator_function  = rsx_momentum_exhaustion, 
                col_name = ['rsx', 'rsx_me_ob', 'rsx_me_os'], 
                mfi_length = self.mfi_length, 
                ob_level = self.ob_level, 
                os_level = self.os_level)
            , 
        ]

    def checkLongSignal(self, i):
        return self.df['rsx_me_os'][i]

    def checkShortSignal(self, i):
        return self.df['rsx_me_ob'][i]

if __name__ == '__main__':
    exchange = Binance()
    df = exchange.getOHLCV(symbol="ETHUSDT", interval="5m", limit=4000)

    strategy = CustomIndicatorStrategy()
    strategy.setUp(df)

    length = len(df['close'])
    longs = [(strategy.df['time'][i], strategy.df['close'][i]) 
        for i in range(length) if strategy.checkLongSignal(i)]

    shorts = [(strategy.df['time'][i], strategy.df['close'][i]) 
        for i in range(length) if strategy.checkShortSignal(i)]

    # These are for plotting
    plotting_indicators = [
		dict(name="rsx", title="RSX", mode="lines", color='lightblue', yaxis='y3', xvalue='date')
    ]
    # print(strategy.df['rsx'])
    # print(strategy.df['rsx_me_ob'])
    # print(strategy.df['rsx_me_os'])

    PlotData(df,
        buy_signals=longs,
        sell_signals=shorts,
        plot_indicators=plotting_indicators,
        plot_title="yeah",
        show_plot=True)

