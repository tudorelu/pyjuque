from os.path import abspath, join, pardir
import sys
sys.path.append(abspath(join(abspath(__file__), pardir, pardir)))

from os import getenv
from pprint import pprint
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
okex = CcxtExchange('okex', {
    'apiKey': getenv('OKEX_API_KEY'), 
    'secret': getenv('OKEX_API_SECRET'),
    'password': getenv('OKEX_PASSWORD'),
    'timeout': 30000,
    'verbose': True,
    'enableRateLimit': True,
})

binance = CcxtExchange('binance', {
    'apiKey': getenv('BINANCE_API_KEY'), 
    'secret': getenv('BINANCE_API_SECRET'),
    'timeout': 30000,
    'verbose': True,
    'enableRateLimit': True,
})
# binance.placeStopLossMarketOrder('ETH/BTC', 'sell', 0.08, 0.025)

def Main():
    exchange = CcxtExchange('okex', {
        'apiKey': getenv('OKEX_API_KEY'), 
        'secret': getenv('OKEX_API_SECRET'),
        'password': getenv('OKEX_PASSWORD'),
        'timeout': 30000,
        # 'verbose': True,
        'enableRateLimit': True,
    })

    exchange.placeStopLossMarketOrder('ETH/BTC', 'sell', 0.08, 0.025, custom_id='Hapciu73662')

if __name__ == '__main__':
        Main()