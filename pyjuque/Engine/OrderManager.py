import time
import math
from uuid import uuid4
from sys import exc_info
from pprint import pprint
from traceback import print_exc
from pyjuque.Engine.Models import TABotModel as Bot, PairModel as Pair, OrderModel as Order


def placeNewOrder(exchange, symbol, pair=None, order=None, test_mode=True, order_params=None):
    """ Create Order model and place order to exchange. """
    new_order_model = createOrderModel(symbol, test_mode, order_params, order)
    if not test_mode:
        new_order_response = placeOrderFromOrderModel(exchange, new_order_model)
    else:
        new_order_response = dict(message='success', status='open', filled=0, side=new_order_model.side)
    exchange.updateSQLOrderModel(new_order_model, new_order_response, None)
    return new_order_model


def createOrderModel(symbol, test_mode, order_params, order):
    """ Create Order Model and fill only mandatory params. 
    Other params are filled after order is filled. """
    if 'price' not in order_params:
        order_params['price'] = None
    if 'take_profit_price' not in order_params:
        order_params['take_profit_price'] = None
    if 'stop_price' not in order_params:
        order_params['stop_price'] = None
    if 'is_entry' not in order_params:
        order_params['is_entry'] = False
    if order is None:
        position_id = str(uuid4()).replace('-', '')
        entry_price = None
    elif order is not None:
        position_id = order.position_id
        entry_price = order.entry_price
    new_order_model = Order(
        id = str(uuid4()).replace('-', ''),
        position_id = position_id,
        bot_id = order_params['bot_id'],
        symbol = symbol,
        price = order_params['price'],
        take_profit_price = order_params['take_profit_price'],
        order_type = order_params['order_type'],
        stop_price = order_params['stop_price'],
        original_quantity = order_params['quantity'],
        side = order_params['side'],
        is_entry =  order_params['is_entry'],
        is_test = test_mode,
        entry_price = entry_price,
        last_checked_time = int(round(time.time() * 1000))
    )
    return new_order_model


def placeOrderFromOrderModel(exchange, order_model):
    """ Places orders from db model to exchange."""
    if order_model.order_type == 'limit':
        order_response = exchange.placeLimitOrder(
            order_model.symbol, order_model.side, 
            order_model.original_quantity, order_model.price, 
            order_model.is_test, custom_id=order_model.id)
    if order_model.order_type == 'market':
        order_response = exchange.placeMarketOrder(
            order_model.symbol, order_model.side, 
            order_model.original_quantity, order_model.is_test, 
            custom_id=order_model.id)
    if order_model.order_type == 'stop_loss':
        order_response = exchange.placeStopLossMarketOrder(
            order_model.symbol, order_model.side, 
            order_model.original_quantity, order_model.price, 
            order_model.is_test, custom_id=order_model.id)
    return order_response


def simulateOrderInfo(exchange, order, kline_interval):
    """ Used when BotController is in test mode. 
    Simulates order info returned by exchange."""
    order_status = dict()
    new_last_checked_time = int(round(time.time() * 1000)) # time in ms
    time_diff = new_last_checked_time - order.last_checked_time
    interval_in_ms = exchange.ccxt.parse_timeframe(kline_interval)
    if  time_diff < interval_in_ms:
        candlestick_data = exchange.getOHLCV(order.symbol, kline_interval, 1)
    else:
        minimum_period = int(math.ceil(time_diff / interval_in_ms))
        candlestick_data = exchange.getOHLCV(order.symbol, kline_interval, 
            minimum_period, start_time=order.last_checked_time)

    for _, candle in candlestick_data.iterrows():
        if order.order_type == 'limit':
            if (order.side == 'buy' and candle['low'] < order.price) or \
                (order.side == 'sell' and candle['high'] > order.price):
                order_status['status'] = 'closed'
                order_status['side'] = order.side
                order_status['filled'] = order.original_quantity
                break
        elif order.order_type == 'market':
            order.price = candle['close']
            order_status['status'] = 'closed'
            order_status['side'] = order.side
            order_status['filled'] = order.original_quantity
            break
        elif order.order_type == 'stop_loss':
            if (order.side == 'sell' and candle['low'] < order.price) or \
                (order.side == 'buy' and candle['high'] > order.price):
                order_status['status'] = 'closed'
                order_status['side'] = order.side
                order_status['filled'] = order.original_quantity
                break
    if not order_status:
        order_status['status'] = order.status
        order_status['side'] = order.side
        order_status['filled'] = order.executed_quantity
    order.last_checked_time = new_last_checked_time
    # print('order_status is')
    # pprint(order_status)
    return order_status


def cancelOrder(exchange, order):
    if order.order_type == 'stop_loss':
        return exchange.cancelAlgoOrder(order.symbol, order.id, is_custom_id=True)

    return exchange.cancelOrder(order.symbol, order.id, is_custom_id=True)


# We replaced klineIntervalToMs to exchange.ccxt.parse_timeframe()