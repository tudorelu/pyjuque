import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Plotting.Plotter import PlotData
from pyjuque.Indicators import AddIndicator, HA

import pandas as pd
import plotly.graph_objs as go

def Maine():
		exchange = Binance()
		symbol = 'BTCUSDT'
		df = exchange.getSymbolKlines(symbol, '1d')

		AddIndicator(df, 'sma', 'volma', 'volume', 10)
		signal = df.loc[df['volume'] > 2.4 * df['volma']]

		s_list = [dict(name='S/R', points=[(row['time'], row['high']) if row['close'] > row['open'] else (row['time'], row['low']) for i, row in signal.iterrows()])]
		
		HA(df, ['open', 'high', 'low', 'close'])

		ha_df = df
		ha_df['open'] = df['HA_open']
		ha_df['high'] = df['HA_high']
		ha_df['low'] = df['HA_low']
		ha_df['close'] = df['HA_close']

		lines = []
		last_time = df['time'][len(df)-1]

		for s in s_list[0]['points']:
			line = go.layout.Shape(
				type="line",
				x0=s[0], y0=s[1],
				x1=last_time, y1=s[1],
				)
			lines.append(line)

		PlotData(ha_df, show_plot=True, 
		signals=s_list, plot_shapes=lines,
		plot_indicators=[dict(name='volma', title="Volume MA", yaxis='y2')])


if __name__ == '__main__':
	Maine()