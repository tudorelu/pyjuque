from pprint import pprint
from time import time as timer

from .utils import load_data_from_file
from pyjuque.Backtester import Backtester
from pyjuque.Strategies import EMACrossStrategy

bot_config = {
    'trade_amount' : 100,
    'strategy_class': EMACrossStrategy,
    'strategy_params': {
        'fast_ma_len' : 8, 
        'slow_ma_len' : 30, 
    },
    'fee_percent' : 0.0,
    'take_profit_value' : 10,
    'stop_loss_value': 20,
    'go_long': True,
    'exit_on_short': True
}


def Main():    
    # we initialize the backtester using the config object
    bt = Backtester(bot_config)

    # retreive the data
    df = load_data_from_file('./data/BTCUSD_1m_1k.csv')

    # backtest strategy (and check the run time)
    start_ = timer()
    bt.backtest(df)
    print(f'Backtesting took {timer() - start_}s')
    
    # show plot
    bt.get_plot(add_strategy_indicators=True).show()


if __name__ == '__main__':
    Main()
