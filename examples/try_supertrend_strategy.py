import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from bot.Indicators.SuperTrend import ST
from bot.Exchanges.Binance import Binance
from bot.Plotting.Plotter import PlotData

def Main():
  	
	symbol = "LTCUSDT"
	print("Init binance...")
	binance = Binance()
	print("Getting data from binance...")
	df = binance.getSymbolKlines(symbol, "15m", limit=10000)

	print("Calculating Supertrend...")
	supertrend_df = ST(df, 10, 3)
	supertrend_df_longer = ST(df, 30, 9)

	lower_supertrend = supertrend_df.where(supertrend_df['supertrend'] < supertrend_df['close'])
	upper_supertrend = supertrend_df.where(supertrend_df['supertrend'] > supertrend_df['close'])

	lower_supertrend_longer = supertrend_df_longer.where(supertrend_df_longer['supertrend'] < supertrend_df_longer['close'])
	upper_supertrend_longer = supertrend_df_longer.where(supertrend_df_longer['supertrend'] > supertrend_df_longer['close'])
	
	df['lower_supertrend'] = lower_supertrend['supertrend']
	df['upper_supertrend'] = upper_supertrend['supertrend']
	df['lower_supertrend_longer'] = lower_supertrend_longer['supertrend']
	df['upper_supertrend_longer'] = upper_supertrend_longer['supertrend']

	print("Plotting...")
	PlotData(df, plot_indicators=[
		dict(name='lower_supertrend', title="Lower ST", color='green'), 
		dict(name='upper_supertrend', title="Upper ST", color='red'),
		dict(name='lower_supertrend_longer', title="Lower ST Longer", color='green'), 
		dict(name='upper_supertrend_longer', title="Upper ST Longer", color='red')], show_plot=True)


if __name__ == '__main__':
		Main()