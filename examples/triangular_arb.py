#######################################################################
#                       TRIANGULAR ARBITRAGE
#######################################################################
#
# Find groups of three coins (A, B and C) that you can trade amongst 
# themselves such that, starting in one coin, after three trades you 
# can find yourself holding a little bit more of the starting coin.
#
#######################################################################
#                        EXPLICIT EXAMPLE
#######################################################################
#
# The coins: BTC, ETH and USDT
#-----------------------------
#
# The sequences, starting with BTC:
#
# 1. BTC -> ETH -> USDT -> BTC
# or
# 2. BTC -> USDT -> ETH -> BTC
#-----------------------------
#
# The trades:
# 
# For 1.    -> SELL BTCETH 
#           -> SELL ETHUSDT 
#           -> BUY BTCUSDT
#
# For 2.    -> SELL BTCUSDT 
#           -> BUY ETHUSDT
#           -> BUY BTCETH
#-----------------------------
# If starting with ETH or USDT, shift the order of the trades by 1.
#-----------------------------
#######################################################################
#                   What this piece of code does
#######################################################################
#
# Issue 1) Identify all the possible triplets, sequences and trades.
#
# Issue 2) Upon updating the order book of pair S, efficiently 
#       calculate the potential profits from initiating a tri-arb 
#       trade where one of the pairs is S
#
# Issue 3) Upon identifying a potential tri-arb trade, save it in a
#       local store; then, figure a way to decide whether to enact it
#       or not, considering that by the time your orders arrive to the
#       exchange, the arbitrage might be gone.
#
#######################################################################
#                         CONSIDERATIONS
#######################################################################
#
# Consideration 1A: The arbitrage might be there for a short
#       amount of time, thus we need to act fast. The slowest part of 
#       this scheme is communicating our orders to the exchange. One 
#       thing we could do is to test out differnet cloud based VMs to 
#       see which ones communicate fastest to the exchange, and deploy
#       our bot there.
#
# Consideration 1B: In order to make the order placing even 
#       faster, we could place at least two orders simultaneously 
#       - if we already hold two of the three pairs of which the arb.
#
# Consideration 2: The arbitrage might be there because of a 
#       spoofing order, in which case we could place a IOC (immediate-
#       or-cancel) order type to start the trade. 
#
#       If the order gets filled, we place the other 2 orders simulta-
#       neously, according to Consideration 1B, because we should be
#       holding both assets - one from the IOC order, the other due to
#       choosing a triplet of which we were already holding 2 coins. 
#       To make this work, the IOC order should not be a trade between
#       the two coins which we are already holding.
#
#######################################################################

import os
import sys
import time
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
  os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

import pprint
from uuid import uuid4
from pprint import pprint
from yaspin import yaspin
from decimal import Decimal, Context
from traceback import print_exc
from contextlib import contextmanager

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Exchanges.BinanceOrderBook import OrderBook
from pyjuque.Engine.Models import Order, getSession, getScopedSession

sp = None
ob = None
session = None
exchange = None

# Settings
starting_coins = [ 'BTC', 'ETH', 'USDT', 'BNB' ] # The coins to maximize 
trade_quantities = dict( 
              ETH = Decimal('0.1'),   # Trading quantities per coin
              BTC = Decimal('0.002'), 
              BNB = Decimal('1'), 
              USDT = Decimal('25'))

# Global Variables
trading_fee = Decimal('0.001')
trading_procedures = dict()

def onUpdateOB(symbol=None):
    
    ordb = ob.getOrderBook()

    symbol_procedures = trading_procedures[symbol]

    for starting_coin in symbol_procedures.keys():
        if starting_coin in starting_coins:
            for triplet in symbol_procedures[starting_coin]:
                pprint(triplet)
                profit, pq1, pq2, pq3 = computeProfit(
                    exchange, starting_coin, trade_quantities[starting_coin],
                    triplet['symbols'], triplet['actions'])
                    
                # profit = calculateProfit(triplet)

                # if profit is not None and profit > trade_quantities[starting_coin]:
                print("{} found on {} \n".format(profit, symbol))
    
def findTriplets(exchange, symbol, desired_assets=None):
    """
    Find all the triplets on an exchange (IE the exchange 
    allows trading between A/B, B/C and C/A) 
    #### Returns
    List of triplets, each triplet being a list of 3 symbols 
    `[A/B, B/C, C/A]` and a list of 3 assets `[A, B, C]` plus 
    a list of all the unique assets in all the triplets.
    """
    unique_symbols = []
    triplets = []

    all_symbols = exchange.SYMBOL_DATAS.keys()

    sd = exchange.SYMBOL_DATAS[symbol]
    base_asset = sd['baseAsset']
    quote_asset = sd['quoteAsset']
    for symbol_2 in all_symbols:
        if symbol != symbol_2 and exchange.SYMBOL_DATAS[symbol_2]["status"] == "TRADING":
            sd2 = exchange.SYMBOL_DATAS[symbol_2]
            base_asset_2 = sd2['baseAsset']
            quote_asset_2 = sd2['quoteAsset']

            potential_symbol_a = None
            potential_symbol_b = None

            if base_asset == base_asset_2:
                potential_symbol_a = quote_asset + quote_asset_2
                potential_symbol_b = quote_asset_2 + quote_asset
            
            elif base_asset == quote_asset_2:
                potential_symbol_a = base_asset_2 + quote_asset
                potential_symbol_b = quote_asset + base_asset_2

            elif quote_asset == base_asset_2:
                potential_symbol_a = base_asset + quote_asset_2
                potential_symbol_b = quote_asset_2 + base_asset

            elif quote_asset == quote_asset_2:
                potential_symbol_a = base_asset + base_asset_2
                potential_symbol_b = base_asset_2 + base_asset
            
            if potential_symbol_a != None:
                symbol_3 = None
                symbol_4 = None

                if exchange.SYMBOL_DATAS.__contains__(potential_symbol_a):
                    if exchange.SYMBOL_DATAS[potential_symbol_a]["status"] == "TRADING":
                        symbol_3 = potential_symbol_a
                if exchange.SYMBOL_DATAS.__contains__(potential_symbol_b):
                    if exchange.SYMBOL_DATAS[potential_symbol_b]["status"] == "TRADING":
                        symbol_4 = potential_symbol_b

                if symbol_3 != None:
                    symbs = [symbol, symbol_2, symbol_3]
                    asst = [base_asset, base_asset_2, quote_asset, quote_asset_2]
                    unique_symbols.extend(symbs)
                    symbs.sort()
                    res = dict(symbols=symbs, assets=list(set(asst)))
                    if res not in triplets:
                        if desired_assets != None:
                            for asset in asst:
                                if asset in desired_assets:
                                    triplets.append(res)
                                    break
                        else:
                            triplets.append(res)
                elif symbol_4 != None:
                    symbs = [symbol, symbol_2, symbol_4] 
                    asst = [base_asset, base_asset_2, quote_asset, quote_asset_2]
                    unique_symbols.extend(symbs)
                    symbs.sort()
                    res = dict(symbols=symbs, assets=list(set(asst)))
                    if res not in triplets:
                        if desired_assets != None:
                            for asset in asst:
                                if asset in desired_assets:
                                    triplets.append(res)
                                    break
                        else:
                            triplets.append(res)
        
    return triplets, set(unique_symbols)

def populateTradingProcedures(triplets):
  """ Given a list of triplets (3 different symbols comprised of 3 and 
  only 3 different assets) create the trading procedures that can be 
  undertaken for profits and populate `trading_procedures` with them.

  #### Example
    For symbols [A/B, B/C, C/A]` and assets `[A, B, C]` we will have 
    the following procedures:
    Starting with A:
      A -> B -> C -> A and A -> C -> B -> A
    Starting with B:
      B -> C -> A -> B and B -> A -> C -> B
    Starting with C:
      C -> A -> B -> C and C -> B -> A -> C
  """

  for triplet in triplets:
    for symbol in triplet['symbols']:
      if not trading_procedures.__contains__(symbol):
        trading_procedures[symbol] = dict()

    # Rotate through all 3 symbols of triplets such
    # that each symbol takes its turn in being first

    if None in triplet['assets']:
      print("None found in assets!")
      pprint(triplet)
      continue
    if None in triplet['symbols']:
      print("None found in symbols!")
      pprint(triplet)
      continue

    asset_1 = triplet['assets'][0]
    asset_2 = triplet['assets'][1]
    asset_3 = triplet['assets'][2]
    for i in range(3):  
      symbol_1 = triplet['symbols'][(0+i)%3]
      symbol_2 = triplet['symbols'][(1+i)%3]
      symbol_3 = triplet['symbols'][(2+i)%3]

      sd1 = exchange.SYMBOL_DATAS[symbol_1]
      sd2 = exchange.SYMBOL_DATAS[symbol_2]
      sd3 = exchange.SYMBOL_DATAS[symbol_3]

      first_asset, second_asset, third_asset = None, None, None
      first_symbol, second_symbol, third_symbol = None, None, None
      first_action, second_action, third_action = None, None, None

      first_asset = asset_1
      first_symbol = symbol_1

      if first_asset in [sd1["baseAsset"], sd1["quoteAsset"]]:
        if asset_2 in [sd1["baseAsset"], sd1["quoteAsset"]]:
          second_asset, third_asset = asset_2, asset_3
        elif asset_3 in [sd1["baseAsset"], sd1["quoteAsset"]]:
          second_asset, third_asset = asset_3, asset_2

        first_action = "SELL" if first_asset == sd1['baseAsset'] else "BUY"

        if second_asset in [sd2["baseAsset"], sd2["quoteAsset"]] \
          and third_asset in [sd2["baseAsset"], sd2["quoteAsset"]]:
          assert third_asset in [sd3["baseAsset"], sd3["quoteAsset"]] \
            and first_asset in [sd3["baseAsset"], sd3["quoteAsset"]], \
            "third {} and first {} should be in {} ".format(
              third_asset, first_asset, symbol_3)
          second_symbol, third_symbol = symbol_2, symbol_3

          second_action = "SELL" if second_asset == sd2['baseAsset'] else "BUY"
          third_action = "SELL" if third_asset == sd3['baseAsset'] else "BUY"

        elif second_asset in [sd3["baseAsset"], sd3["quoteAsset"]] \
          and third_asset in [sd3["baseAsset"], sd3["quoteAsset"]]:
          assert third_asset in [sd2["baseAsset"], sd2["quoteAsset"]] \
            and first_asset in [sd2["baseAsset"], sd2["quoteAsset"]], \
            "third {} and first {} should be in {} ".format(
              third_asset, first_asset, symbol_2)
          second_symbol, third_symbol = symbol_3, symbol_2
          
          second_action = "SELL" if second_asset == sd3['baseAsset'] else "BUY"
          third_action = "SELL" if third_asset == sd2['baseAsset'] else "BUY"

        for symb in [first_symbol, second_symbol, third_symbol]:
          if not trading_procedures[symb].__contains__(first_asset):
            trading_procedures[symb][first_asset] = []
          trading_procedures[symb][first_asset].append(dict(
            assets=[first_asset, second_asset, third_asset],
            symbols=[first_symbol, second_symbol, third_symbol],
            actions=[first_action, second_action, third_action]
          ))

          if not trading_procedures[symb].__contains__(second_asset):
            trading_procedures[symb][second_asset] = []
          trading_procedures[symb][second_asset].append(dict(
            assets=[second_asset, third_asset, first_asset],
            symbols=[second_symbol, third_symbol, first_symbol],
            actions=[second_action, third_action, first_action]
          ))
          
          if not trading_procedures[symb].__contains__(third_asset):
            trading_procedures[symb][third_asset] = []
          trading_procedures[symb][third_asset].append(dict(
            assets=[third_asset, first_asset, second_asset],
            symbols=[third_symbol, first_symbol, second_symbol],
            actions=[third_action, first_action, second_action]
          ))

def calculateProfit(triplet):

    assets = triplet['assets']
    actions = triplet['actions']
    symbols = triplet['symbols']
    # coin_1 = assets[0] # coin_2 = assets[1] # coin_3 = assets[2]
    # pair_1 = symbols[0] # pair_2 = symbols[1] # pair_3 = symbols[2]

    coin_1, coin_2, coin_3 = assets
    pair_1, pair_2, pair_3 = symbols
    sd_1 = exchange.SYMBOL_DATAS[pair_1]
    sd_2 = exchange.SYMBOL_DATAS[pair_2]
    sd_3 = exchange.SYMBOL_DATAS[pair_3]

    quantity_1 = trade_quantities[coin_1]

    if coin_1 == sd_1['baseAsset']:
        pass
    elif coin_1 == sd_1['quoteAsset']:
        quantity_1 = Decimal('1') / trade_quantities[coin_1]


def computeProfit(exchange, starting_coin, quantity, symbols, actions):
  """ Compute Actual Profit based on order book data for the movement of 
  `starting_coin` (IE USDT) between 'symbols' ['BTCUSDT', 'MITHBTC', 'MITHUSDT'] 
  given by `actions` ['BUY', 'BUY', 'SELL'] """

  sd1 = exchange.SYMBOL_DATAS[symbols[0]]
  sd2 = exchange.SYMBOL_DATAS[symbols[1]]
  sd3 = exchange.SYMBOL_DATAS[symbols[2]]

  # print(starting_coin, quantity, symbols, actions)
  # print('cp1')
  # trade_1_quantity = (
  #   Decimal(100 - PER_TRADE_PERCENTAGE_FEES) / Decimal(100)) \
  # * Decimal(quantity)
  coin_1_quantity = Decimal(quantity) 

  # print('cp2')
  try:
    trade_1_avg_price = ob.getOrderBookPrice(
      exchange = exchange,
      symbol = symbols[0],
      side = actions[0],
      quantity = coin_1_quantity,
      is_quote_quantity = (starting_coin==sd1['quoteAsset']))
  except Exception:
    # print_exc()
    # print("ERR1")
    # my_printer.pprint(order_book[symbols[0]])
    return None, None, None, None

  print("Coin 1 {}, Symbol {}, trade_1_price: {} qty: {}".format(starting_coin, symbols[0], trade_1_avg_price, coin_1_quantity))

  if starting_coin == sd1['quoteAsset']:
    coin_1_quantity = Decimal(coin_1_quantity) / Decimal(trade_1_avg_price)
  else:
    coin_1_quantity = Decimal(coin_1_quantity) * Decimal(trade_1_avg_price)
  
  coin_1_quantity = exchange.toValidQuantity(symbols[0], coin_1_quantity)

  coin_2 = symbols[0].replace(starting_coin, '')
  coin_2_quantity = coin_1_quantity

  print("Coin 1 {}, Symbol {}, trade_1_price: {} qty: {}".format(starting_coin, symbols[0], trade_1_avg_price, coin_1_quantity))
  
  # print('cp4')
  try:
    trade_2_avg_price = ob.getOrderBookPrice(
      exchange=exchange,
      symbol=symbols[1],
      side=actions[1],
      quantity=coin_2_quantity,
      is_quote_quantity=(coin_2 == sd2['quoteAsset']))
  except Exception:
    # print_exc()
    # print("ERR2")
    return None, None, None, None

  if coin_2 == sd2['quoteAsset']:
    coin_2_quantity = Decimal(coin_2_quantity) / Decimal(trade_2_avg_price)
  else:
    coin_2_quantity = Decimal(coin_2_quantity) * Decimal(trade_2_avg_price)

  coin_2_quantity = exchange.toValidQuantity(symbols[1], coin_2_quantity)

  coin_3 = symbols[1].replace(coin_2, '')
  coin_3_quantity = coin_2_quantity

  print("Coin 2 {}, Symbol {}, trade_2_price: {} qty: {}".format(coin_2, symbols[1], trade_2_avg_price, coin_2_quantity))
  try:
    trade_3_avg_price = ob.getOrderBookPrice(
      exchange=exchange,
      symbol=symbols[2],
      side=actions[2],
      quantity=coin_3_quantity,
      is_quote_quantity=(coin_3 == sd3['quoteAsset']))
  except Exception:
    # print_exc()
    # print("ERR3")
    return None, None, None, None

  if coin_3 == sd3['quoteAsset']:
    coin_3_quantity = Decimal(coin_3_quantity) / Decimal(trade_3_avg_price)
  else:
    coin_3_quantity = Decimal(coin_3_quantity) * Decimal(trade_3_avg_price)

  coin_3_quantity = exchange.toValidQuantity(symbols[2], coin_3_quantity)
  print("Coin 3 {}, Symbol {}, trade_3_price: {} qty: {}".format(coin_3, symbols[2], trade_3_avg_price, coin_3_quantity))

  print("1 price: {}, 1 qty: {}, 2 price: {}, 2 qty: {}, 3 price: {}, 3 qty: {}".format(
      trade_1_avg_price, coin_1_quantity, 
      trade_2_avg_price, coin_2_quantity, 
      trade_3_avg_price, coin_3_quantity))

  final_qty = coin_3_quantity

  # print("cp5")
  return final_qty, \
    (trade_1_avg_price, coin_1_quantity), \
    (trade_2_avg_price, coin_2_quantity), \
    (trade_3_avg_price, coin_3_quantity)

if __name__ == '__main__':

    exchange = Binance(get_credentials_from_env=True)
    # session = Session()

    # pprint(exchange.SYMBOL_DATAS["XEMBNB"])

    ethbtc_trip, us = findTriplets(exchange, symbol="ETHBTC")

    xemeth_trip, unique_symbols = findTriplets(exchange, symbol="XEMETH")

    # pprint(ethbtc_trip)
    # pprint(xemeth_trip)

    populateTradingProcedures(xemeth_trip)
    # print()
    # pprint(trading_procedures)
    print(unique_symbols)

    sp = yaspin()
    ob = OrderBook(symbols=unique_symbols, onUpdate=onUpdateOB, msUpdate=False)
    time.sleep(5)
    ob.startOrderBook()
    time.sleep(5)
    sp.start()
