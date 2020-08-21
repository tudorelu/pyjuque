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
from bot.Utils import dotdict
from bot.Strategies.StrategyOptimiser import StrategyOptimiser
from pprint import pprint
from decimal import Decimal

entry_strategy:dotdict = dotdict(dict(
	strategy_class = BBRSIStrategy,
	args = (8, 100, 60, 40),
))

entry_settings:dotdict = dotdict(dict(

))

exit_settings:dotdict = dotdict(dict( 
	pt = 1.025, 
	sl = 0.9
))

def Main():
	# Initialize exchanges and test
	symbol = "LTCUSDT"
	binance = Binance()
	sd = binance.SYMBOL_DATAS[symbol]
	df = binance.getSymbolKlines(symbol, "15m", limit=10000)
	
	def fitness_function(individual):
		pt = round(Decimal(int(individual[4])) / Decimal(1000), 3)
		entry_strategy.args = tuple(individual[0:4])
		exit_settings.pt = pt
		results = backtest(df, sd, binance, entry_strategy, entry_settings, exit_settings)
		return float(results['total_profit_loss'])

	optimiser = StrategyOptimiser(
		fitness_function=fitness_function,
		n_generations=30,
		generation_size=50,
		n_genes=5,
		gene_ranges=[(3, 40), (15, 80), (60, 100), (0, 40), (1004, 1150)],
		mutation_probability=0.3,
		gene_mutation_probability=0.5,
		n_select_best=15
	)

	best_children = optimiser.run_genetic_algo()
	pprint(best_children)

if __name__ == '__main__':
	Main()