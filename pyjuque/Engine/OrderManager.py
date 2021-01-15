import time
import math
from uuid import uuid4
from pprint import pprint
from pyjuque.Engine.Models import TABot as Bot, Pair, Order

# This may be in the Order Manager
def placeNewOrder(exchange, symbol, pair, order=None, test_mode=True, order_params=None):
    """ Create Order model and place order to exchange. """

    # print("2: Order params are")
    # pprint(order_params)
    new_order_model = createOrderModel(symbol, test_mode, order_params, order)

    if not test_mode:
        new_order_response = placeOrderFromOrderModel(exchange, new_order_model)
    else:
        new_order_response = dict(message='success')

    if exchange.isValidResponse(new_order_response):
        exchange.updateSQLOrderModel(
            new_order_model, new_order_response, None)
        return new_order_model

# This would be in the Order Manager
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
        position_id = str(uuid4())
        entry_price = None
    elif order is not None:
        position_id = order.position_id
        entry_price = order.entry_price

    new_order_model = Order(
                    id = str(uuid4()),
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

# This would be in the Order Manager
def placeOrderFromOrderModel(exchange, order_model):
    """ Places orders from db model to exchange."""
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

# This would be in the Order Manager
def simulateOrderInfo(exchange, order, kline_interval):
    """ Used when BotController is in test mode. 
    Simulates order info returned by exchange."""
    order_status = dict()
    new_last_checked_time = int(round(time.time() * 1000)) # time in ms
    time_diff = new_last_checked_time - order.last_checked_time
    interval_in_ms = klineIntervalToMs(kline_interval)
    if  time_diff < interval_in_ms:
        candlestick_data = exchange.getOHLCV(
            order.symbol, kline_interval, 1)
    else:
        minimum_period = int(math.ceil(time_diff / interval_in_ms))
        candlestick_data = exchange.getOHLCV(
            order.symbol, kline_interval, 
            minimum_period, start_time=order.last_checked_time)

    for _, candle in candlestick_data.iterrows():
        lowest_price = candle['low']
        if order.order_type == exchange.ORDER_TYPE_LIMIT:
            if lowest_price <= order.price:
                order_status['status'] = exchange.ORDER_STATUS_FILLED
                order_status['side'] = order.side
                order_status['executedQty'] = order.original_quantity
                break
        elif order.order_type == exchange.ORDER_TYPE_MARKET:
            # not sure what to set this value to. 
            # For now average of open and close of candle.
            order.price = (candle['open'] + candle['close'])/2
            order_status['status'] = exchange.ORDER_STATUS_FILLED
            order_status['side'] = order.side
            order_status['executedQty'] = order.original_quantity
            break
        elif order.order_type == exchange.ORDER_TYPE_STOP_LOSS:
            if lowest_price >= order.price:
                order_status['status'] = exchange.ORDER_STATUS_FILLED
                order_status['side'] = order.side
                order_status['executedQty'] = order.original_quantity
                break
    if not order_status:
        order_status['status'] = exchange.ORDER_STATUS_NEW
        order_status['side'] = order.side
        order_status['executedQty'] = 0

    order.last_checked_time = new_last_checked_time
    return order_status

def klineIntervalToMs(kline_interval:str):
    number = int(kline_interval[:-1])
    unit = kline_interval[-1]
    if unit == 'm':
        multiply_by = 1000 * 60
    if unit =='h':
        multiply_by = 1000 * 60 * 60
    if unit == 'd':
        multiply_by = 1000 * 60 * 60 * 24
    if unit == 'w':
        multiply_by = 1000 * 60 * 60 * 24 * 7
    if unit == 'M':
        multiply_by = 1000 * 60 * 60 * 24 * 31 # bit too long does not matter.
    return number * multiply_by