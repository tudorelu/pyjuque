import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from pprint import pprint
from pyjuque.Exchanges.BinanceOrderBook import OrderBook

if __name__ == '__main__':
    ob = OrderBook(symbols=['BTCUSDT', 'LTCUSDT'])

    ob.startOrderBook()
    time.sleep(3)
    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTCUSDT', ordb.__contains__('BTCUSDT'),
        'LTCUSDT', ordb.__contains__('LTCUSDT'),
        'YFIBTC', ordb.__contains__('YFIBTC'),
        'UNIBTC', ordb.__contains__('UNIBTC')
    ))
    ob.subscribeToSymbol("YFIBTC")
    # pprint(ordb)
    time.sleep(10)

    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTCUSDT', ordb.__contains__('BTCUSDT'),
        'LTCUSDT', ordb.__contains__('LTCUSDT'),
        'YFIBTC', ordb.__contains__('YFIBTC'),
        'UNIBTC', ordb.__contains__('UNIBTC')
    ))
    ob.subscribeToSymbol("UNIBTC")
    # pprint(ordb)
    time.sleep(3)
    # pprint(ordb)
    ordb = ob.getOrderBook()
    print("Ordb contains {} : {}, {} : {}, {} : {}, {} : {}".format(
        'BTCUSDT', ordb.__contains__('BTCUSDT'),
        'LTCUSDT', ordb.__contains__('LTCUSDT'),
        'YFIBTC', ordb.__contains__('YFIBTC'),
        'UNIBTC', ordb.__contains__('UNIBTC')
    ))
    pprint(ordb)
    time.sleep(3)
    ob.stopOrderBook()