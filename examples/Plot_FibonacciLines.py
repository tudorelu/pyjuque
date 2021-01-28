import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from pyjuque.Plotting import PlotData
import plotly.graph_objs as go

def horizontal_line(start_time, end_time, value, color=None):
    return go.layout.Shape(
        type="line", 
        x0=start_time, 
        y0=value,
        x1=end_time, 
        y1=value,
        line=dict(color=color)
    )

def Main():
    exchange = CcxtExchange('binance')

    symbol = "BTC/USDT"
    interval = "4h"

    df = exchange.getOHLCVHistory(symbol, interval, 8000)

    start_time = df['time'][0]
    end_time = df['time'][len(df)-1]
    
    price_min = df['close'].min()
    price_max = df['close'].max()
    diff = price_max - price_min
    level1 = price_max - 0.236 * diff
    level2 = price_max - 0.382 * diff
    level3 = price_max - 0.618 * diff
    lines = []
    lines.append(horizontal_line(
        start_time, end_time, price_max, 
        color="rgba(255, 0, 0, 255)"))
    lines.append(horizontal_line(
        start_time, end_time, level1, 
        color="rgba(255, 255, 0, 255)"))
    lines.append(horizontal_line(
        start_time, end_time, level2, 
        color="rgba(0, 255, 0, 255)"))
    lines.append(horizontal_line(
        start_time, end_time, level3, 
        color="rgba(0, 255, 255, 255)"))
    lines.append(horizontal_line(
        start_time, end_time, price_min, 
        color="rgba(0, 0, 255, 255)"))

    PlotData(df, 
        add_candles=False, 
        plot_shapes=lines,
        plot_title="fib_levels_"+symbol.replace('/', '').lower() + "_" + interval, 
        show_plot=True)


if __name__ == '__main__':
    Main()