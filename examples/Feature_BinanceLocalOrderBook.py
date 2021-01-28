from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)

import time
from pprint import pprint
from pyjuque.Exchanges.BinanceOrderBook import OrderBook

if __name__ == '__main__':
    ob = OrderBook(symbols=['BTC/USDT', 'LTC/USDT'])

    ob.startOrderBook()
    time.sleep(3)
    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTCUSDT', ordb.__contains__('BTC/USDT'),
        'LTCUSDT', ordb.__contains__('LTC/USDT'),
        'YFIBTC', ordb.__contains__('YFI/BTC'),
        'UNIBTC', ordb.__contains__('UNI/BTC')
    ))
    ob.subscribeToSymbol("YFI/BTC")
    # pprint(ordb)
    time.sleep(10)

    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTC/USDT', ordb.__contains__('BTC/USDT'),
        'LTC/USDT', ordb.__contains__('LTC/USDT'),
        'YFI/BTC', ordb.__contains__('YFI/BTC'),
        'UNI/BTC', ordb.__contains__('UNI/BTC')
    ))
    ob.subscribeToSymbol("UNI/BTC")
    # pprint(ordb)
    time.sleep(3)
    # pprint(ordb)
    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTC/USDT', ordb.__contains__('BTC/USDT'),
        'LTC/USDT', ordb.__contains__('LTC/USDT'),
        'YFI/BTC', ordb.__contains__('YFI/BTC'),
        'UNI/BTC', ordb.__contains__('UNI/BTC')
    ))
    pprint(ordb)
    time.sleep(3)
    ob.stopOrderBook()