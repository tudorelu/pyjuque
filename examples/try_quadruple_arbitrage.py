##############################
#   QUADRUPTE ARBITRAGE
##############################
#
# Start with coin A and make four trades to get back to A
# If the final amount is higher than the initial amount, 
# you have an arbitrage.
#
##############################
#   EXPLICIT EXAMPLE
##############################
#
# 'BTC' -> 'NGN' -> 'USDT' -> 'IDRT' -> 'BTC'
#
# sell pair 'BTCNGN', 
# then buy 'USDTNGN'
# then sell 'USDTIDRT' 
# finally buy 'BTCIDRT'
#
# Values of Interest
#
#       bid of 'BTCNGN' = bid_1
#       ask of 'usdtngn' = ask_2 
#       bid of 'usdtidrt' = bid_3 
#       ask of 'btcidrt' = ask_4
#
# ONE 'BTC' -> 0.999 * bid_1 'NGN' (after fees)
# ONE 'BTC' -> x_1 'NGN
#
# ONE 'NGN' -> 0.999 / ask_2 'USDT' (after fees)
# x_1 'NGN' -> (0.999)^2 * bid_2 / ask_2 'USDT'
# x_1 'NGN' -> x_2 'USDT'
#
# ONE 'USDT' -> 0.999 * bid_3 'IDRT' (after fees)
# x_2 'USDT' ->  (0.999)^3 * bid_1 * bid_3 / ask_2 'IDRT'
# x_2 'USDT' -> x_3 'IDRT'
#
# ONE 'IDRT' -> 0.999 / ask_4 'BTC' (after fees)
# x_3 'IDRT' -> (0.999)^4 * bid_1 * bid_3 / ask_2 * ask_4 'BTC'
# x_3 'IDRT' -> x_4 'BTC'
#
# ONE 'BTC' -> x_4 'BTC'
#
# if 1 < x_4, you have an arb on your hands.
##############################


import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
  os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

from uuid import uuid4
from pprint import pprint
from yaspin import yaspin
from decimal import Decimal
from contextlib import contextmanager

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Exchanges.BinanceOrderBook import OrderBook
from pyjuque.Engine.Models import Order, getSession, getScopedSession

sp = None
ob = None
session = None
exchange = None

# Session = getScopedSession('sqlite:///quad_arb.db')

symbols = ['BTCNGN', 'BTCIDRT', 'BTCUSDT', 'USDTNGN', 'USDTIDRT']

trading_fee = 0.001

def onUpdateOB():
    
    ordb = ob.getOrderBook()
    bid_1 = Decimal(ordb['BTCNGN']['bids'][0][0])
    ask_2 = Decimal(ordb['USDTNGN']['asks'][0][0])
    bid_3 = Decimal(ordb['USDTIDRT']['bids'][0][0])
    ask_4 = Decimal(ordb['BTCIDRT']['asks'][0][0])

    fee_multiplier = (Decimal(1) - Decimal(trading_fee)) * (Decimal(1) - Decimal(trading_fee))\
        * (Decimal(1) - Decimal(trading_fee)) * (Decimal(1) - Decimal(trading_fee))

    result = fee_multiplier * bid_1 * bid_3 / (ask_2 * ask_4) 

    # print(fee_multiplier, bid_1, ask_2, bid_3, ask_4)
    profit_percentage = result * Decimal(100) - Decimal(100)
    if result > Decimal(1):
        sp.start()
        print("ARB! Could make {}%".format(round(profit_percentage, 2)))
        sp.start()
    else:
        sp.text = "Losing about {}%".format(round(profit_percentage, 2))
    

def placeOrderFromOrderModel(order_model, exchange):
    """ Places orders from db model to exchange."""
    order_response = dict(code="err")
    if order_model.order_type == exchange.ORDER_TYPE_LIMIT:
        order_response = exchange.placeLimitOrder(
            order_model.symbol, order_model.price, 
            order_model.side, order_model.original_quantity, 
            order_model.is_test, custom_id=order_model.id)
    if order_model.order_type == exchange.ORDER_TYPE_MARKET:
        order_response = exchange.placeMarketOrder(
            order_model.symbol, order_model.side, 
            order_model.original_quantity, order_model.is_test, 
            custom_id=order_model.id)
    if order_model.order_type == exchange.ORDER_TYPE_STOP_LOSS:
        order_response = exchange.placeStopLossMarketOrder(
            order_model.symbol, order_model.price, 
            order_model.side, order_model.original_quantity, 
            order_model.is_test, custom_id=order_model.id)
    return order_response
    
if __name__ == '__main__':

    exchange = Binance(get_credentials_from_env=True)
    # session = Session()

    sp = yaspin()
    ob = OrderBook(symbols=symbols, onUpdate=onUpdateOB, msUpdate=False)
    ob.startOrderBook()
    time.sleep(5)
    sp.start()
