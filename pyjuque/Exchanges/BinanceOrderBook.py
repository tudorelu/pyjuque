"""
Description:
  Creates a Local Order Book and updates it every second via a 
  WebSocket connection to Binance

"""
from os import getenv
import time
import json 
import datetime
import websocket 
import threading
from pprint import pprint
from decimal import Decimal, Context

from pyjuque.Exchanges.Binance import Binance
from pyjuque.Exchanges.CcxtExchange import CcxtExchange

############## GLOBAL VARIABLES ##############

ws = None                             # Websocket Object
exchange = CcxtExchange('binance', {
    'apiKey': getenv('BINANCE_API_KEY'), 
    'secret': getenv('BINANCE_API_SECRET'),
    'timeout': 30000,
    'enableRateLimit': True,
})      
# The exchange
order_book = dict(counter = 0)        # The (per-symbol) order book
order_book_lock = threading.Lock()    # Order book threading lock
order_book_initialized = dict()       # Whether the (per-symbol) local 
                                      #   order book was initialized
buffered_events = dict(counter = 0)   # Buffers events before local 
                                      #   order book initialization
############## FOR COUNTING ##############
buffered_events_count = 0
unbuffered_events_count = 0

def onOpen(ws):
  print('Opened connection')

def onClose(ws):
  print('Closed connection')

def onError(ws, error):
  print('Got an error')
  print(error)

def onMessage(ws, message):
  json_message = json.loads(message)
  # pprint(json_message['data']['s'])
  symbol = json_message['data']['s']
  global order_book_initialized
  if not order_book_initialized[symbol]:
    global order_book_lock, buffered_events, buffered_events_count
    # print("Got event")
    order_book_lock.acquire()
    # print("Buffering event")
    buffered_events_count += 1
    buffered_events[symbol].append(json_message)
    order_book_lock.release()
  else:
    # print("{}s order book already unlocked".format(symbol))
    global order_book, exchange
    if json_message['data']['u'] < order_book[symbol]['lastUpdateId']:
      pass
      # print("Received older event. Discarding it.")
    else:
      new_asks = insertAsks(
        order_book[symbol]['asks'], json_message['data']['a'])
      new_bids = insertBids(
        order_book[symbol]['bids'], json_message['data']['b'])
      order_book[symbol]['lastUpdateId'] = json_message['data']['u']
      order_book['counter'] += 1

      order_book[symbol]['asks'] = new_asks
      order_book[symbol]['bids'] = new_bids

def insertAsks(previous_asks, received_asks):
  """ Inserts multiple new asks in the order book (assumes 
  that the order book AND the new_asks list are sorted)"""

  new_asks = []

  if len(received_asks) < 1:
    return previous_asks
  if len(previous_asks) < 1:
    return received_asks
  
  # print("Prev")
  # pprint(previous_asks)
  # print("Recv")
  # pprint(received_asks)

  # Uses the merge-sort idea of popping the first element in the lists
  # (which should also be the lowest)
  while len(previous_asks) > 0 and len(received_asks) > 0:
    ask = None
    if Decimal(previous_asks[0][0]) < Decimal(received_asks[0][0]):
      ask = previous_asks.pop(0)
      # print('popped from prev')
    elif Decimal(previous_asks[0][0]) > Decimal(received_asks[0][0]):
      # print('popped from recv')
      ask = received_asks.pop(0)
    else:
      # print('equal, popped from both')
      previous_asks.pop(0)
      ask = received_asks.pop(0)
    
    # print(ask)

    if Decimal(ask[1]) > Decimal(0):
      # print("appended")
      new_asks.append(ask)

  # print("After Merge")
  # pprint(new_asks)

  if len(previous_asks) > 0:
    new_asks.extend(previous_asks)
  elif len(received_asks) > 0:
    new_asks.extend(received_asks)
  
  # print("Complete")
  # pprint(new_asks)

  return new_asks

def insertBids(previous_bids, received_bids):
  """ Inserts multiple new bids in the order book (assumes 
  that the order book AND the new_bids list are sorted)"""

  new_bids = []

  while len(previous_bids) > 0 and len(received_bids) > 0:
    bid = None
    if Decimal(previous_bids[0][0]) > Decimal(received_bids[0][0]):
      bid = previous_bids.pop(0)
    elif Decimal(previous_bids[0][0]) < Decimal(received_bids[0][0]):
      bid = received_bids.pop(0)
    else:
      previous_bids.pop(0)
      bid = received_bids.pop(0)
    
    if Decimal(bid[1]) > Decimal(0):
      new_bids.append(bid)

  if len(previous_bids) > 0:
    new_bids.extend(previous_bids)
  elif len(received_bids) > 0:
    new_bids.extend(received_bids)

  return new_bids

class UpdateOrderBookThread(threading.Thread):
  """ Thread that connects to exchange through websocket and updates 
  local order book """
  def __init__(self, name, socket_url, onUpdate=None):
    threading.Thread.__init__(self)
    self.name = name
    self.socket_url = socket_url
    self.onUpdate = onUpdate

  def run(self):
    print("Start Running")
    print(self.socket_url)

    # websocket.enableTrace(True)
    msg = onMessage
    if self.onUpdate != None:
      def onMessageUpdated(ws, message):
        onMessage(ws, message)
        symbol = None
        try:
          json_message = json.loads(message)
          symbol = json_message['data']['s']
        except:
          print("Exception getting symbol from ws message.")
          pass
        self.onUpdate(symbol)
      msg = onMessageUpdated

    global ws

    ws = websocket.WebSocketApp(
      self.socket_url, 
      on_close=onClose, 
      on_error=onError,
      on_message=msg)
    ws.on_open=onOpen
    ws.run_forever()

class CreateOrderBookThread(threading.Thread):
  """ Thread that collects order book data from exchange and 
  initializes local order book """
  def __init__(self, name, exchange, symbols):
    threading.Thread.__init__(self)
    self.name = name
    self.symbols = symbols
    self.exchange = exchange

  def run(self):
    global order_book, buffered_events, unbuffered_events_count
    global order_book_lock, order_book_initialized, buffered_events_count
    time.sleep(2)
    for symbol in self.symbols:
      ob = self.exchange.getOrderBook(symbol, 50)
    #   print('OB IS')
    #   pprint(order_book)
      order_book[symbol] = dict(
        lastUpdateId=ob['lastUpdateId'], 
        bids=ob['bids'], 
        asks=ob['asks'])

      order_book_lock.acquire()
      unbuffered_events_count += len(buffered_events[symbol])
      for i, event in enumerate(buffered_events[symbol]):
        if event['data']['u'] <= order_book[symbol]['lastUpdateId']:
          pass
        else:
          order_book[symbol]['asks'] = insertAsks(
            order_book[symbol]['asks'], event['data']['a'])
          order_book[symbol]['bids'] = insertBids(
            order_book[symbol]['bids'], event['data']['b'])
        order_book[symbol]['lastUpdateId'] = event['data']['u']
      
      order_book_initialized[symbol] = True
      order_book_lock.release()
      print("total: {}, {}: {} unbuffered".format(
        buffered_events_count, symbol, len(buffered_events[symbol])))

class OrderBook():
  def __init__(self, symbols, onUpdate=None, msUpdate=False):
    self.symbols = symbols
    self.onUpdate = onUpdate
    self.msUpdate = msUpdate

  def startOrderBook(self):
    global buffered_events, order_book_initialized, exchange
    msg = "Creating order books holding {} symbols."\
      .format(len(self.symbols))
    print(msg)
    for symbol in self.symbols:
      buffered_events[symbol] = []
      order_book_initialized[symbol] = False
    streams = []
    if self.msUpdate:
      streams = [ symbol.replace('/', '').lower()+"@depth@100ms" for symbol in self.symbols ]
    else:
      streams = [ symbol.replace('/', '').lower()+"@depth" for symbol in self.symbols ]
    socket_url = "wss://stream.binance.com:9443/stream?streams=" + \
      '/'.join(streams)
    update_order_book_thread = UpdateOrderBookThread(
      "UpdateOrderBook", socket_url, self.onUpdate)
    create_order_book_thread = CreateOrderBookThread(
      "CreateOrderBook", exchange, self.symbols)
    update_order_book_thread.start()
    create_order_book_thread.start()

  def getOrderBook(self, symbol=None):
    global order_book
    if symbol == None:
      return order_book
    
    if order_book.__contains__(symbol):
      return order_book[symbol]
    
    return None
  
  def stopOrderBook(self):
    global ws
    ws.close()

  def subscribeToSymbol(self, symbol):
    global ws, exchange, order_book_initialized, buffered_events
    speed = "100ms" if self.msUpdate else ""
    msg = {
        "method": "SUBSCRIBE",
        "params":
        [
            "{}@depth{}".format(symbol.replace('/', '').lower(), speed)
        ],
        "id": 1
    }
    ws.send(json.dumps(msg))
    buffered_events[symbol] = []
    order_book_initialized[symbol] = False
    create_order_book_thread = CreateOrderBookThread(
      "CreateOrderBook_{}".format(symbol), exchange, [symbol])
    create_order_book_thread.start()

  def unsubscribeFromSymbol(self, symbol):
    global ws
    speed = "100ms" if self.msUpdate else ""
    msg = {
        "method": "UNSUBSCRIBE",
        "params":
        [
            "{}@depth{}".format(symbol.replace('/', '').lower(), speed)
        ],
        "id": 2
    }
    ws.send(json.dumps(msg))


  def getOrderBookPrice(self, exchange, symbol, side, quantity, is_quote_quantity):
    """ Calculates the average price we would pay / receive per unit of `symbol` 
    if we wanted to trade `quantity` of that `symbol`, based on its order book"""
    global order_book
    initial_quantity = quantity

    symbol_order_book = order_book[symbol]
    order_book_side = symbol_order_book['asks'] \
      if side == 'buy' else symbol_order_book['bids']

    i, orders, price = 0, [], Decimal('0')
    accounted_for_quantity = Decimal('0')

    qtdif = Decimal('1')
    while qtdif > Decimal('0'):
      order = order_book_side[i]
      if is_quote_quantity:
        qty = min(Decimal(order[1]) * Decimal(order[0]), quantity - accounted_for_quantity)
      else:
        qty = min(Decimal(order[1]), quantity - accounted_for_quantity)
      
      price += (Decimal(order[0]) * qty)
      accounted_for_quantity += Decimal(qty)
      qtdif = abs(quantity - accounted_for_quantity)
      i += 1


    #   print("Step {}, qty {}, qtdiff {}, price_point {}, price {}".format(i, qty, qtdif, order[0], price))

    # print("Price {}, qty {}".format(price, quantity))
    return price / quantity
