import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from bot.Strategies.SimpleOneStrategy import SimpleOneStrategy
from bot.Strategies.SimpleTwoStrategy import SimpleTwoStrategy
from bot.Strategies.OTTStrategy import OTTStrategy
from bot.Exchanges.Binance import Binance
from bot.Plotter import PlotData

def Main():
	exchange = Binance()
	symbol = 'BNBUSDT'
	df = exchange.getSymbolKlines(symbol, '1h', 500)
	strategy = OTTStrategy(1, 0.1)
	strategy.setup(df)

	signals=[
		dict(points=strategy.getBuySignalsList(), name="buy_times"),
		dict(points=strategy.getSellSignalsList(), name="sell_times")]

	df['ott'] = df['ott'].shift(2)
	PlotData(df, plot_indicators=strategy.getIndicators(), signals=signals,
		show_plot=True, plot_title="SmoothrngStrategy")

if __name__ == '__main__':
	Main()