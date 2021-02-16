from os.path import abspath, join, pardir
import sys
sys.path.append(abspath(join(abspath(__file__), pardir, pardir)))

from os import getenv
from pprint import pprint
from pyjuque.Exchanges.CcxtExchange import CcxtExchange


def Main():
    exchange = CcxtExchange('okex', {
        'apiKey': getenv('OKEX_API_KEY'), 
        'secret': getenv('OKEX_API_SECRET'),
        'password': getenv('OKEX_PASSWORD'),
        'timeout': 30000,
        # 'verbose': True,
        'enableRateLimit': True,
    })

    exchange.placeStopLossMarketOrder('ETH/BTC', 'sell', 0.08, 0.025, custom_id='your_custom_id_here')

if __name__ == '__main__':
        Main()