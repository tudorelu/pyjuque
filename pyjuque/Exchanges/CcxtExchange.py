import ccxt
import pandas as pd
from pprint import pprint
from decimal import Decimal
from datetime import datetime

class CcxtExchange():

    def __init__(self, exchange_id, params):
        self.exchange_id = exchange_id # 'binance'
        self.exchange_class = getattr(ccxt, exchange_id)
        self.exchange = self.exchange_class(params)
        # params = {
        #     'apiKey': 'YOUR_API_KEY',
        #     'secret': 'YOUR_SECRET',
        #     'timeout': 30000,
        #     'enableRateLimit': True,
        # }


    def getOHLCV(self, symbol, interval, limit=1000, start_time=None, cast_to=float):
        """ Converts cctx ohlcv data from list of lists to dataframe. """
        ohlcv = self.exchange.fetchOHLCV(
            symbol, interval, since=start_time, limit=limit)
        df = pd.DataFrame(ohlcv)
        df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        # transform values from strings to floats
        for col in df.columns:
            df[col] = df[col].astype(cast_to)
        df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)
        return df


    def placeOrder(self, symbol, params, test=False): 
        """ 
        Places order on exchange given a dictionary of parameters.
        """

        return self.exchange.createOrder(symbol, params)


    def placeMarketOrder(self, symbol, side, amount, test=False, custom_id=False):
        """ 
        Places side (buy/sell) market order for amount of symbol.
        """
        args = dict()

        if custom_id:
            args['clientOrderId'] = custom_id

        order = self.exchange.createOrder(
            symbol=symbol, type='market', side=side, 
            amount=amount, price=None, params=args)
        
        return order


    def placeLimitOrder(self, symbol, side, amount, price, test=False, custom_id=False):
        """ 
        Places side (buy/sell) limit order for amount of symbol at price. 
        """
        
        args = dict()

        if custom_id:
            args['clientOrderId'] = custom_id

        order = self.exchange.createOrder(
            symbol=symbol, type='limit', side=side, 
            amount=amount, price=price, params=args)
        
        return order


    def placeStopLossMarketOrder(self, symbol, price, side, amount, test=False, custom_id=False):
        """ Places a STOP_LOSS market order for amount of symbol at price. """
        raise NotImplementedError


    def cancelOrder(self, symbol, order_id, is_custom_id=False):
        """ Cancels order given order id """
        params = {}
        if is_custom_id:
            params['clientOrderId'] = order_id

        return self.exchange.cancelOrder(order_id, symbol, params)


    def getOrder(self, symbol, order_id, is_custom_id=False):
        """ Gets order given order id """
        params = {}
        if is_custom_id:
            params['clientOrderId'] = order_id

        return self.exchange.fetchOrder(order_id, symbol, params)


    def updateSQLOrderModel(self, order, order_response, bot):
        """ 
        Updates an order based on it's state on the exchange given by 
        order_response. Should be part of the exchange interface  """

        print("Order response is")
        pprint(order_response)
        if order.is_test:
            if order.side == 'buy':
                order.entry_price = order.price

        if not order.is_test:
            if order_response['timestamp'] is not None:
                order.timestamp = datetime.fromtimestamp(
                    order_response['timestamp'] / 1000)
            if order_response['price'] is not None:
                order.price = order_response['price']
            if order_response['amount'] is not None:
                order.original_quantity =  Decimal(order_response['amount'])
            if order_response['filled'] is not None:
                order.executed_quantity =  Decimal(order_response['filled'])
            if order_response['status'] is not None:
                order.status = order_response['status']
            if order_response['side'] is not None:
                order.side = order_response['side']
            if order_response['type'] is not None:
                order.order_type = order_response['type']
            if order.side == 'buy':
                order.entry_price = order_response['price']

        return order
