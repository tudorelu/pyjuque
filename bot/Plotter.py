import pandas as pd
import requests
import json

import plotly.graph_objs as go
from plotly.offline import plot

"""
	This file contains all the tools used for plotting data.

	It currently contains only one function, a general purpose plotting function
	which plots candlestick charts, overlayed with indicators, signals, & 
	trendlines.

	Eventually, there should be more functions here, each of which would solve a 
	single purpose, to provide more flexibility to developers as to what to plot 
	and how to style it. Modular is the aim.
"""

# Generic Plotting Function
def PlotData(df, 
	buys = False, 
	sells = False, 
	plot_title:str = "",
	trendlines = False,
	indicators=[
		dict(col_name="50_ema", color="indianred", name="50 EMA"), 
		dict(col_name="200_ema", color="navyblue", name="200 EMA")],
	export_plot = False):
	""" Generic Plotting Function
		
		Params
		--
			df 	
				dataframe containing OHLCV data (open, high, low, close, 
				volume) might also contain technical indicators, which can 
				be plotted if they also appear in the indicators parameter
			buys 
				list of (time, price) tuples for the buy signals (mainly 
				used for backtesting)
			sells 
				list of (time, price) tuples for the sell signals (mainly 
				used for backtesting)
			plot_title
				Title of the plot
			trendlines
			indicators
				List of dicts containing info about what indicators to plot 
				& their styling (indicators need to be present in the df in 
				order to be plotted)

		Returns
		--
			Plotly Figure

	"""

	# Create Candlestick Chart
	candle = go.Candlestick(
		x = df['time'],
		open = df['open'],
		close = df['close'],
		high = df['high'],
		low = df['low'],
		name = "Candlesticks")

	data = [candle]

	# Add Indicators
	for item in indicators:
		if df.__contains__(item['col_name']):
			fsma = go.Scatter(
				x = df['time'],
				y = df[item['col_name']],
				name = item['name'],
				line = dict(color = (item['color'])))
			data.append(fsma)

	# Add Signals
	if buys:
		buys = go.Scatter(
				x = [item[0] for item in buys],
				y = [item[1] for item in buys],
				name = "Buy Signals",
				mode = "markers",
				marker_size = 20
			)
		data.append(buys)

	if sells:
		sells = go.Scatter(
			x = [item[0] for item in sells],
			y = [item[1] for item in sells],
			name = "Sell Signals",
			mode = "markers",
			marker_size = 20
		)
		data.append(sells)

	# Configure Style and Display (check plotly documentation)
	layout = go.Layout(
		title=plot_title,
		xaxis = {
			"title" : plot_title,
			"rangeslider" : {"visible": False},
			"type" : "date"
		},
		yaxis = {
			"fixedrange" : False,
		})

	if trendlines is not False:
		layout['shapes'] = trendlines
		
	fig = go.Figure(data = data, layout = layout)

	if export_plot:
		plot(fig, filename=plot_title+'.html')
	
	return fig
