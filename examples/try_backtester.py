import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

# Import all Created exchanges here
from bot.Exchanges.Binance import Binance
from pandas import DataFrame

from bot.Strategies.BBRSIStrategy import BBRSIStrategy
from bot.Backtester import backtest
from bot.Plotter import PlotData

from pprint import pprint

from bot.Utils import dotdict
		
entry_strategy:dotdict = dotdict(dict(
	strategy_class = BBRSIStrategy,
	args = (8, 100, 60, 40),
))

entry_settings:dotdict = dotdict(dict(
	# subsequent entries
	se = dotdict(dict(
		times = 1,
		after_profit = 0.99,	
		pt_decrease = 0.998,
	))
))

exit_settings:dotdict = dotdict(dict( 
	# pt = 1.045, 
	# trailins stop loss
	tsl = dotdict(dict(
		value = 0.985,
		after_profit = 1.015
	)),
	# stop loss
	sl = 0.9
))

def Main():
	# Initialize exchanges and test
	binance = Binance()
	symbol = "LTCUSDT"
	sd = binance.SYMBOL_DATAS[symbol]
	df = binance.getSymbolKlines(symbol, "1m", limit=3000)
	results = backtest(df, sd, binance, entry_strategy, entry_settings, exit_settings)

	pprint(results['total_profit_loss'])
	strategy = entry_strategy.strategy_class(*entry_strategy.args)
	strategy.setup(df)

	signals=[
		dict(points=results['buy_times'], name="buy_times"),
		dict(points=results['tp_sell_times'], name="tp_sell_times"),
		dict(points=results['sl_sell_times'], name="sl_sell_times"),
		dict(points=results['tsl_sell_times'], name="tsl_sell_times"),
		dict(points=results['tsl_active_times'], name="tsl_active_times"),
		dict(points=results['tsl_increase_times'], name="tsl_increase_times")]

	PlotData(df, signals=signals, plot_indicators=strategy.getIndicators(), 
	save_plot=True, show_plot=True)

if __name__ == '__main__':
	Main()