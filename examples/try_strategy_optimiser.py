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
from bot.Engine.Backtester import backtest
from bot.Plotter import PlotData
from bot.Utils import dotdict

# from examples.strategy_optimiser_ga import *
from bot.Strategies.StrategyOptimiser import StrategyOptimiser
from pprint import pprint
from decimal import Decimal

entry_strategy:dotdict = dotdict(dict(
	strategy_class = BBRSIStrategy,
	args = (8, 100, 60, 40),
))

entry_settings:dotdict = dotdict(dict(
	# subsequent entries
	# se = dotdict(dict(
	# 	times = 1,
	# 	after_profit = 0.99,	
	# 	pt_decrease = 0.998,
	# ))
))

exit_settings:dotdict = dotdict(dict( 
	pt = 1.025, 
	# trailins stop loss
	# tsl = dotdict(dict(
	# 	value = 0.985,
	# 	after_profit = 1.015
	# )),
	# stop loss
	sl = 0.9
))

def Main():
	# Initialize exchanges and test
	symbol = "LTCUSDT"
	binance = Binance()
	sd = binance.SYMBOL_DATAS[symbol]
	df = binance.getSymbolKlines(symbol, "1h", limit=1000)
	
	def fitness_function(individual):
		pt = round(Decimal(int(individual[4])) / Decimal(1000), 3)
		entry_strategy.args = tuple(individual[0:4])
		exit_settings.pt = pt
		results = backtest(df, sd, binance, entry_strategy, entry_settings, exit_settings)
		# print("Individual", individual, float(results['total_profit_loss']))
		return float(results['total_profit_loss'])
	
	print("Running Genetic Algo")
	optimiser = StrategyOptimiser(
		fitness_function,	
		n_generations = 20, 
		generation_size = 50,
		n_genes = 5, 
		gene_ranges=[(3, 15), (20, 80), (60, 100), (0, 40), (1005, 1100)], 
		mutation_probability = 0.3, 
		gene_mutation_probability = 0.5, 
		n_select_best = 10
	)
	optimiser.run_genetic_algo()

	print("Done running genetic algo.")


if __name__ == '__main__':
	Main()