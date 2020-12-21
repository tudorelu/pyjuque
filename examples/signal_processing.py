import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pprint import pprint
from decimal import Decimal

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Plotting.Plotter import PlotData
import pandas as pd
import pandas_ta as ta

from scipy import signal

exchange = Binance()

df = exchange.getSymbolKlines('BTCUSDT', '1m', 1000)
df['sma_5'] = df.ta.sma(length=5)
pprint(df)

sos = signal.butter(10, 300, 'lowpass', fs=1000, output='sos')
filtered = signal.sosfilt(sos, df['sma_5'])
df['filtered_sma_1'] = filtered

sos = signal.butter(1, 1/120, 'lowpass', fs=1/60, output='sos')
filtered = signal.sosfilt(sos, df['sma_5'])
df['filtered_sma_2'] = filtered

pprint(df)

plotting_indicators = [
    dict(name="sma_5", title="SMA 10", mode="lines", color='red'),
    dict(name="filtered_sma_1", title="Filtered SMA 10", mode="lines", color='orange'),
    dict(name="filtered_sma_2", title="Filtered SMA 10", mode="lines", color='green'),
]


PlotData(
    df,
    plot_indicators=plotting_indicators,
    plot_title="BTCUSDT",
    show_plot=True)
