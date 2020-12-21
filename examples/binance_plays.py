import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from uuid import uuid4
from pprint import pprint
# from yaspin import yaspin
from decimal import Decimal
from contextlib import contextmanager

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Exchanges.BinanceOrderBook import OrderBook
from pyjuque.Engine.Models import Order, getSession
from datetime import datetime

session = getSession('sqlite:///liquidity_provider_11.db')
exchange = Binance(get_credentials_from_env=True)
orders = session.query(Order).all()

for order in orders:
    order_info = exchange.getOrder(
        symbol = order.symbol, order_id = order.id, is_custom_id = True)

    start_time = datetime.fromtimestamp(order_info['time']/1000)
    end_time = datetime.fromtimestamp(order_info['updateTime']/1000)

    print("Order started at {} and was {} at {}, {} seconds later".format(
        start_time, order_info['status'], end_time,
        round((end_time - start_time).total_seconds())
    ))

    if Decimal(order_info['executedQty']) > Decimal(0):
        print("\n")
        pprint(order_info)
        
    print("\n")

    time.sleep(5)