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

symbols = ['COTIBTC']


settings = {
    'COTIBTC' : {
        'btc_amount' : Decimal(0.0187), 
        'min_distance_from_bid_before_replace' : 0.0045,
        'max_distance_from_bid_before_replace' : 0.012,
        'max_distance_from_ask_before_replace' : 0.036,
        'new_order_distance_from_bid': 0.006,
        'distance_above_buy_price': 0.0023
    },
    'ALGOBTC' : {
        'btc_amount' : Decimal(0.009), 
        'min_distance_from_bid_before_replace' : 0.006,
        'max_distance_from_bid_before_replace' : 0.012,
        'max_distance_from_ask_before_replace' : 0.036,
        'new_order_distance_from_bid': 0.008,
        'distance_above_buy_price': 0.0023
    },
    'HARDUSDT' : {
        'btc_amount' : Decimal(0.014), 
        'min_distance_from_bid_before_replace' : 0.0085,
        'max_distance_from_bid_before_replace' : 0.014,
        'max_distance_from_ask_before_replace' : 0.04,
        'new_order_distance_from_bid': 0.01,
        'distance_above_buy_price': 0.004
    },
    'XEMETH' : {
        'btc_amount' : Decimal(0.025), 
        'min_distance_from_bid_before_replace' : 0.0044,
        'max_distance_from_bid_before_replace' : 0.012,
        'max_distance_from_ask_before_replace' : 0.036,
        'new_order_distance_from_bid': 0.0055,
        'distance_above_buy_price': 0.003
    },
    'COTIBNB' : {
        'btc_amount' : Decimal(0.0047), 
        'min_distance_from_bid_before_replace' : 0.004,
        'max_distance_from_bid_before_replace' : 0.008,
        'max_distance_from_ask_before_replace' : 0.04,
        'new_order_distance_from_bid': 0.0044,
        'distance_above_buy_price': 0.0034
    }
}

refresh_bid_order_time = 5

sp = None
ob = None
session = None
exchange = None

Session = getScopedSession('sqlite:///liquidity_provider_17.db')

def onUpdateOB():
    
    ordb = ob.getOrderBook()
    db_session = Session()

    sp_text = "{}".format(round(time.time(), 1))
    for symbol in symbols:
        
        if not ordb.__contains__(symbol):
            break

        symbol_ob = ordb[symbol]
        symbol_orders = db_session.query(Order).filter_by(
            symbol=symbol, is_closed=0).all()
        
        sp_text += " | "+symbol+": "
        
        # Initializing the arams for this symbol
        min_dbbr = settings[symbol]['min_distance_from_bid_before_replace']
        max_dbbr = settings[symbol]['max_distance_from_bid_before_replace']
        
        for order in symbol_orders:

            if order.status == exchange.ORDER_STATUS_CANCELED:
                sp_text += "order canceled.".format(symbol)
            else:
                if order.side == exchange.ORDER_SIDE_BUY:
                    distance_in_percent = Decimal(100) \
                        * Decimal(symbol_ob["bids"][0][0]) / order.price \
                        - Decimal(100)

                    replace_order = False
                    if order.price * Decimal(1.0 + min_dbbr) \
                        > Decimal(symbol_ob["bids"][0][0]):
                        sp_text += "less than {}% away from bid, replace".format(
                            round(min_dbbr * 100, 2))
                        replace_order = True
                    elif order.price * Decimal(1.0 + max_dbbr) \
                        < Decimal(symbol_ob["bids"][0][0]):
                        sp_text += "more than {}% away from bid, replace".format(
                            round(max_dbbr * 100, 2))
                        replace_order = True

                    if not replace_order:
                        sp_text += "{}% to buy ".format(round(distance_in_percent, 2))

                    if replace_order:
                        response = exchange.cancelOrder(
                            symbol=symbol, 
                            order_id=order.id, 
                            is_custom_id=True)

                        if exchange.isValidResponse(response):
                            order.status = exchange.ORDER_STATUS_CANCELED
                            db_session.commit()

                elif order.side == exchange.ORDER_SIDE_SELL:
    
                    distance_in_percent = Decimal(100) \
                        * order.price / Decimal(symbol_ob["asks"][0][0]) \
                        - Decimal(100)
                    sp_text += "{}% to sell ".format(
                        round(distance_in_percent, 2))
                    
    sp.text = sp_text
    Session.remove()

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
    session = Session()
    
    all_orders = session.query(Order).all()

    for order in all_orders:
        if order.is_closed == 0:
            exchange_order_info = exchange.getOrder(
                symbol=order.symbol, order_id=order.id, is_custom_id=True)
            if exchange.isValidResponse(exchange_order_info):
                # pprint(exchange_order_info)
                exchange.updateSQLOrderModel(order, exchange_order_info, None)
                if order.status in [exchange.ORDER_STATUS_CANCELED]:
                    order.is_closed = 1
            else:
                print("Invalid exchange response when checking order status.")
                pprint(exchange_order_info)
                print()

    session.commit()
    
    # time.sleep(100)
    sp = yaspin()
    ob = OrderBook(symbols=symbols, onUpdate=onUpdateOB, msUpdate=True)
    ob.startOrderBook()
    time.sleep(5)
    sp.start()
    # Every x seconds, cancel existing BUY orders and update them to be
    # exactly 1% below last bid. If any past order was filled, place a 
    # sell order for the same amount at x % above it.
    while True:
        
        # print("Looping through orders...")
        ordb = ob.getOrderBook()
        exchange.updateTickerData()
        # pprint(ordb)
        for symbol in symbols:
            if not ordb.__contains__(symbol):
                break

            symbol_ob = ordb[symbol]
            symbol_orders = session.query(Order).filter_by(
                symbol=symbol, is_closed=0).all()
            entered = False

            # Initializing the params for this symbol
            min_dbbr = settings[symbol]['min_distance_from_bid_before_replace']
            max_dbbr = settings[symbol]['max_distance_from_bid_before_replace']
            max_dabr = settings[symbol]['max_distance_from_ask_before_replace']
            nodfb = settings[symbol]['new_order_distance_from_bid']
            take_profit_percentage = settings[symbol]['distance_above_buy_price']

            for order in symbol_orders:
                entered = True
                exchange_order_info = exchange.getOrder(
                    symbol=order.symbol, order_id=order.id, is_custom_id=True)
                if exchange.isValidResponse(exchange_order_info):
                    exchange.updateSQLOrderModel(order, exchange_order_info, None)
                else:
                    sp.text = "Invalid exchange response when checking order status."
                    "Not updating order at this time."
                    break
                session.commit()

                if order.side == exchange.ORDER_SIDE_BUY:
                    distance_in_percent = Decimal(100) \
                        * Decimal(symbol_ob['bids'][0][0]) / order.price \
                        - Decimal(100)
                    sp.text = "{}: Distance between order and first bid is {}%".format(
                        symbol, round(distance_in_percent, 2))

                    replace_order = False
                    if order.price * Decimal(1.0 + min_dbbr) \
                        > Decimal(symbol_ob['bids'][0][0]):
                        sp.stop()
                        print("\n{}: Order is less than {}% away from last bid "
                            "price. if unfilled, cancel and place new one. \n".format(
                                symbol, round(min_dbbr * 100, 2)))
                        sp.start()
                        replace_order = True
                    elif order.price * Decimal(1.0 + max_dbbr) \
                        < Decimal(symbol_ob['bids'][0][0]):
                        sp.stop()
                        print("\n{}: Order is more than {}% away from last bid "
                            "price. if unfilled, cancel and place new one. \n".format(
                                symbol, round(max_dbbr * 100, 2)))
                        sp.start()
                        replace_order = True
                    
                    if order.status == exchange.ORDER_STATUS_CANCELED:
                        replace_order = True

                    if replace_order:
                        response = dict(msg="success")
                        if order.status not in [exchange.ORDER_STATUS_FILLED,
                            exchange.ORDER_STATUS_CANCELED]:
                            response = exchange.cancelOrder(
                                symbol=symbol, 
                                order_id=order.id, 
                                is_custom_id=True)
                    
                        # First, cancel old order
                        if exchange.isValidResponse(response):
                            if order.status != exchange.ORDER_STATUS_FILLED:
                                order.status = exchange.ORDER_STATUS_CANCELED
                                session.commit()
                            
                            executedQty = order.executed_quantity
                            originalQty = order.original_quantity
                            got_rid_of_excess_amount = False
                            
                            # If canceled succesfuly
                            if executedQty > Decimal(0): 
                                desired_price = order.price \
                                    * Decimal(1.0 + take_profit_percentage)
                                new_sell_order = Order(
                                    id=str(uuid4()),
                                    symbol=symbol, 
                                    entry_price=order.price,
                                    price=desired_price, 
                                    side=exchange.ORDER_SIDE_SELL,
                                    order_type=exchange.ORDER_TYPE_LIMIT,
                                    original_quantity=executedQty)

                                sp.stop()
                                response_2 = placeOrderFromOrderModel(
                                    new_sell_order, exchange)
                                if exchange.isValidResponse(response_2):
                                    got_rid_of_excess_amount = True
                                    order.is_closed = 1
                                    exchange.updateSQLOrderModel(
                                        new_sell_order, response_2, None)
                                    session.add(new_sell_order)
                                    session.commit()
                                else:
                                    print("Invalid response placing new sell order.")
                                    pprint(response_2)
                                    print()
                                sp.start()
                            else:
                                got_rid_of_excess_amount = True
                                order.is_closed = 1
                                session.commit()
                                  
                            if got_rid_of_excess_amount:
                                symbol_data = exchange.SYMBOL_DATAS[symbol]
                                base_asset = symbol_data["baseAsset"]
                                quote_asset = symbol_data["quoteAsset"]
                                ord_price = Decimal(symbol_ob['bids'][0][0]) \
                                    * Decimal(1 - nodfb)
                                ord_quantity = settings[symbol]['btc_amount'] / ord_price
                                if quote_asset != "BTC":
                                    base_price_btc = exchange.getPriceInBTC(base_asset)
                                    ord_quantity = settings[symbol]['btc_amount'] / base_price_btc

                                if executedQty > Decimal(0):
                                    ord_quantity = ord_quantity \
                                        * (Decimal(1) - executedQty / originalQty)
                                else:
                                    for order_2 in symbol_orders:
                                        if order_2.id != order.id and order.is_closed == False:
                                            if order_2.status not in [exchange.ORDER_STATUS_FILLED, 
                                                exchange.ORDER_STATUS_CANCELED]:
                                                ord_quantity = ord_quantity - order_2.original_quantity

                                new_buy_order = Order(
                                    id=str(uuid4()),
                                    symbol=symbol, 
                                    price=ord_price, 
                                    side=exchange.ORDER_SIDE_BUY,
                                    order_type=exchange.ORDER_TYPE_LIMIT,
                                    original_quantity=ord_quantity)

                                sp.stop()
                                response_2 = placeOrderFromOrderModel(
                                    new_buy_order, exchange)
                                if exchange.isValidResponse(response_2):
                                    # Closing Initial Order
                                    exchange.updateSQLOrderModel(
                                        new_buy_order, response_2, None)
                                    session.add(new_buy_order)
                                    session.commit()
                                else:
                                    print("Invalid response placing new buy order.")
                                    pprint(response_2)
                                    print()
                                sp.start()
                        else:
                            sp.stop()
                            print("Invalid response when trying to cancel order.")
                            pprint(response)
                            print()
                            sp.start()

                elif order.side == exchange.ORDER_SIDE_SELL:

                    distance_in_percent = Decimal(100) \
                        * order.price / Decimal(symbol_ob['asks'][0][0]) \
                        - Decimal(100)
                    sp.text = "{}: Distance between order and first ask is {}%".format(
                        symbol, round(distance_in_percent, 2))
                    
                    # SELL ORDER FILLED MEANS WE EXITED IT AT A PROFIT
                    if order.status == exchange.ORDER_STATUS_FILLED:
                        sp.stop()
                        print("\nFilled sell order, placing a new buy order!\n")

                        symbol_data = exchange.SYMBOL_DATAS[symbol]
                        base_asset = symbol_data["baseAsset"]
                        quote_asset = symbol_data["quoteAsset"]
                        ord_price = Decimal(symbol_ob['bids'][0][0]) \
                            * Decimal(1 - nodfb)
                        ord_quantity = order.executed_quantity \
                            * order.price / ord_price  

                        print("Base {}, Quote {}, price {}, quantity {}".format(
                            base_asset, quote_asset, ord_price, ord_quantity))
                        buy_order = Order(
                            id=str(uuid4()),
                            symbol=symbol, 
                            price=ord_price, 
                            side=exchange.ORDER_SIDE_BUY,
                            order_type=exchange.ORDER_TYPE_LIMIT,
                            original_quantity=ord_quantity)

                        response = placeOrderFromOrderModel(buy_order, exchange)
                        if exchange.isValidResponse(response):
                            exchange.updateSQLOrderModel(
                                buy_order, response, None)
                            order.is_closed = True

                            session.add(buy_order)
                            session.commit()
                            
                            init_quote_qty_btc = order.price \
                                * order.executed_quantity
                                
                            tp_quote_qty_btc = buy_order.price \
                                * order.executed_quantity

                            if quote_asset != "BTC":
                                quote_price_btc = exchange.getPriceInBTC(quote_asset)
                                init_quote_qty_btc = init_quote_qty_btc * quote_price_btc
                                tp_quote_qty_btc = tp_quote_qty_btc * quote_price_btc
                                
                            settings[symbol]['btc_amount'] = settings[symbol]['btc_amount'] \
                                + (init_quote_qty_btc - tp_quote_qty_btc)
                            
                            print("Added an extra amount of {} BTC for each order,"
                                "trading amount for {} is now {}".format(
                                init_quote_qty_btc - tp_quote_qty_btc,
                                symbol, settings[symbol]['btc_amount']))
                        else:
                            print("Invalid response when placing initial buy order.")
                            pprint(response)
                            print()
                        sp.start()

                    # IF NOT FILLED AND DISTANCE LARGER THAN OUR STOP 
                    # LOSS, EXIT AT A LOSS :-()
                    elif distance_in_percent > Decimal(100) * Decimal(max_dabr):

                        sp.stop()
                        print("\nSTOP LOSS {}: Order is more than {}% away from last ask "
                            "price, cancel and place new one.\n".format(
                                symbol, round(max_dabr * 100, 2)))
                        # First, cancel old order
                        response = dict(msg="success")
                        if order.status not in [exchange.ORDER_STATUS_FILLED,
                            exchange.ORDER_STATUS_CANCELED]:
                            response = exchange.cancelOrder(
                                symbol=symbol, 
                                order_id=order.id, 
                                is_custom_id=True)
                    
                        if exchange.isValidResponse(response):
                            executedQty = order.executed_quantity
                            originalQty = order.original_quantity
                            stop_loss_sell_order = Order(
                                id=str(uuid4()),
                                symbol=symbol, 
                                price=Decimal(symbol_ob['bids'][4][0]), 
                                side=exchange.ORDER_SIDE_SELL,
                                order_type=exchange.ORDER_TYPE_LIMIT,
                                original_quantity=originalQty - executedQty)
                            
                            response_2 = placeOrderFromOrderModel(
                                stop_loss_sell_order, exchange)
                            if exchange.isValidResponse(response_2):
                                exchange.updateSQLOrderModel(
                                    stop_loss_sell_order, response_2, None)
                                order.is_closed = True
                                                                    
                                session.add(stop_loss_sell_order)
                                session.commit()
                                
                                init_quote_qty_btc = order.entry_price \
                                    * stop_loss_sell_order.original_quantity

                                sl_quote_qty_btc = stop_loss_sell_order.price \
                                    * stop_loss_sell_order.original_quantity

                                symbol_data = exchange.SYMBOL_DATAS[symbol]
                                quote_asset = symbol_data["quoteAsset"]

                                if quote_asset != "BTC":
                                    quote_price_btc = exchange.getPriceInBTC(quote_asset)
                                    sl_quote_qty_btc = sl_quote_qty_btc * quote_price_btc
                                    init_quote_qty_btc = init_quote_qty_btc * quote_price_btc
                                
                                settings[symbol]['btc_amount'] = settings[symbol]['btc_amount'] \
                                    - (init_quote_qty_btc - sl_quote_qty_btc)
                                
                                print("Removed an extra amount of {} BTC from each order, "\
                                    "trading amount for {} is now {}".format(
                                    (init_quote_qty_btc - sl_quote_qty_btc),
                                    symbol, settings[symbol]['btc_amount']))

                        sp.start()

            if not entered:
                symbol_data = exchange.SYMBOL_DATAS[symbol]
                base_asset = symbol_data["baseAsset"]
                quote_asset = symbol_data["quoteAsset"]
                ord_price = Decimal(symbol_ob['bids'][0][0]) \
                    * Decimal(1 - nodfb)
                ord_quantity = settings[symbol]['btc_amount'] / ord_price

                if quote_asset != "BTC":
                    base_price_btc = exchange.getPriceInBTC(base_asset)
                    ord_quantity = settings[symbol]['btc_amount'] / base_price_btc

                # print("Base {}, Quote {}, price {}, quantity {}".format(
                #     base_asset, quote_asset, ord_price, ord_quantity))
                buy_order = Order(
                    id=str(uuid4()),
                    symbol=symbol, 
                    price=ord_price, 
                    side=exchange.ORDER_SIDE_BUY,
                    order_type=exchange.ORDER_TYPE_LIMIT,
                    original_quantity=ord_quantity)

                sp.stop()
                response = placeOrderFromOrderModel(buy_order, exchange)
                if exchange.isValidResponse(response):
                    exchange.updateSQLOrderModel(
                        buy_order, response, None)
                    session.add(buy_order)
                    session.commit()
                else:
                    print("Invalid response when placing initial buy order.")
                    pprint(response)
                    print()
                sp.start()

        session.commit()
        time.sleep(refresh_bid_order_time)

        # If there are PARTIALLY FILLED buy orders, cancel them and 
        # for each one place a sell order for the executedQty at 0.3% 
        # above it and a buy order at 1% below last bid for the 
        # remaining quantity.


        # If there are UNFILLED(NEW) buy orders between 0.6% and 2% of
        # the last bid, leave them

        # If there are any open buy order less than 0.6% below the last 
        # bid, cancel them and for each one place another one with the 
        # same quantity


        # If there are no open BUY orders, place a buy order at x% 
        # below the last bid.
