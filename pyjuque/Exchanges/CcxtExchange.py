import ccxt
import pandas as pd
from pprint import pprint
from decimal import Decimal
from datetime import datetime
import requests 
import json

class FetchHistoricalDataException(Exception):
    pass

class CcxtExchange():

    def __init__(self, exchange_id, params={}):
        self.exchange_id = exchange_id # 'binance'
        self.exchange_class = getattr(ccxt, exchange_id)
        self.ccxt = self.exchange_class(params)
    

    def getOHLCV(self, symbol, interval, limit=1000, start_time=None, cast_to=float):
        """ Converts cctx ohlcv data from list of lists to dataframe. """
        if start_time != None:
            start_time = int(start_time)
        ohlcv = self.ccxt.fetchOHLCV(
            symbol, interval, since=start_time, limit=limit)
        if len(ohlcv) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(ohlcv)
        df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        # transform values from strings to floats
        for col in df.columns:
            df[col] = df[col].astype(cast_to)
        df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)
        return df



    def getOHLCVHistory(self, symbol, interval, limit=None, start_time=None, cast_to=float):
        """ Converts cctx ohlcv data from list of lists to dataframe. """
        time_now = datetime.timestamp(datetime.now()) * 1000
        if limit != None and limit < 1000:
            return self.getOHLCV(symbol, interval, limit=limit, start_time=start_time, cast_to=cast_to)
        df = self.getOHLCV(symbol, interval, limit=1000, start_time=start_time, cast_to=cast_to)
        if df.empty:
            raise FetchHistoricalDataException(
                '{} doesn\'t provide access to this data.'.format(
                    self.exchange_id))
        time_diff = self.ccxt.parse_timeframe(interval) * 1000
        last_time = df.iloc[-1]['time']
        max_limit = limit
        # print(last_time)
        while last_time + time_diff < time_now:
            l = 1000
            if max_limit != None:
                print(max_limit)
                l = max_limit
                if l >= 1000:
                    l = 1000
                    max_limit = max_limit - 1000
            df2 = self.getOHLCV(symbol, interval, limit=l, start_time=last_time, cast_to=cast_to)
            df = df.append(df2, ignore_index = True)
            last_time = df.iloc[-1]['time']
            if l < 1000:
                return df
            # print(last_time)
            # print(df.loc[len(df)-1])
        return df

    def placeOrder(self, symbol, params, test=False): 
        """ 
        Places order on exchange given a dictionary of parameters.
        """
        return self.ccxt.createOrder(symbol, params)


    def placeMarketOrder(self, symbol, side, amount, test=False, custom_id=False):
        """ 
        Places side (buy/sell) market order for amount of symbol.
        """
        args = dict()
        if custom_id:
            args['clientOrderId'] = custom_id
        # try:
        order = self.ccxt.createOrder(
            symbol=symbol, type='market', side=side, 
            amount=amount, price=None, params=args)
        # except:
        #     return None    
        return order


    def placeLimitOrder(self, symbol, side, amount, price, test=False, custom_id=False):
        """ 
        Places side (buy/sell) limit order for amount of symbol at price. 
        """
        args = dict()
        if custom_id:
            args['clientOrderId'] = custom_id
        # try:
        order = self.ccxt.createOrder(
            symbol=symbol, type='limit', side=side, 
            amount=amount, price=price, params=args)
        # except:
        #     return None
        return order


    def placeStopLossMarketOrder(self, symbol, side, amount, price, test=False, custom_id=False):
        """ Places a STOP_LOSS market order for amount of symbol at price. """
        args = dict()
        if custom_id:
            args['clientOrderId'] = custom_id
        ret = dict()
        if self.exchange_id == 'binance':
            args['stopPrice'] = price
            data = self.ccxt.createOrder(
                symbol=symbol, 
                type='stop_loss_limit', 
                side=side, 
                amount=amount, 
                price=price * 0.98, 
                params=args)
            ret = data
            ret['id'] = data['orderId']
        elif self.exchange_id == 'okex':
            args = {
                'instrument_id' : symbol.replace('/', '-'), 
                'order_type':'1', # trigger
                'mode':'1',     # spot
                'side':side, 
                'size':amount, 
                'trigger_price':price, 
                'algo_type':'2'
                }
            data = self.ccxt.spotPostOrderAlgo(args)
            ret = data
            ret['id'] = data['algo_id']
        else:
            raise NotImplementedError('SL order not implemented for {}'.format(self.exchange_id))
        # print('Placing SL Market order for {} returned'.format(self.exchange_id))
        # pprint(data)
        return ret


    def cancelOrder(self, symbol, order_id, is_custom_id=False):
        """ Cancels order given order id """
        params = {}
        if is_custom_id:
            if self.exchange_id == 'kucoin':
                result = self.ccxt.private_get_orders({'status':'active'})
                orders = result['data']['items']
                for order in orders:
                    if order['clientOid'] == order_id:
                        order_id = order['id']
                        break
            else:
                params['clientOrderId'] = order_id
        return self.ccxt.cancelOrder(order_id, symbol, params)


    def cancelAlgoOrder(self, symbol, order_id, order_type='1', is_custom_id=False):
        params = {}
        if is_custom_id:
            params['clientOrderId'] = order_id
        if self.exchange_id == 'binance':
            # try:
            order = self.ccxt.cancelOrder(order_id, symbol, params)
            # except:
            #     return None
        elif self.exchange_id == 'okex':
            # try:
            data = self.ccxt.spotPostCancelBatchAlgos(
                {
                    'instrument_id':'ETH-BTC', 
                    'algo_ids':[order_id], 
                    'order_type':'1'
                })
            order = data
            # except:
            #     return None
        else:
            raise NotImplementedError('Getting algo orders not implemented for {}'.format(self.exchange_id))
        # print('Canceling algo order for {} returned'.format(self.exchange_id))
        # pprint(order)
        return order


    def getOrder(self, symbol, order_id, is_custom_id=False):
        """ Gets order given order id """ 
        params = {}
        # print('Getting Order {}'.format(order_id))
        if is_custom_id:
            # print('custom id')
            if self.exchange_id == 'kucoin':
                # print('Kucoin, custom id')
                result = self.ccxt.private_get_orders({'status':'active'})
                active_orders = result['data']['items']
                result = self.ccxt.private_get_orders()
                done_orders = result['data']['items']
                # print('kucoin active orders len is {}, done_orders {}'.format(len(active_orders), len(done_orders)))
                for order in active_orders:
                    # pprint(order)
                    if order['clientOid'] == order_id:
                        # print('Found!')
                        # pprint(order)
                        order_id = order['id']
                        break
                for order in done_orders:
                      # pprint(order)
                    if order['clientOid'] == order_id:
                        # print('Found!')
                        # pprint(order)
                        order_id = order['id']
                        break
            else:
                params['clientOrderId'] = order_id
        return self.ccxt.fetchOrder(order_id, symbol, params)
    

    def getAlgoOrder(self, symbol, order_id, order_type='1', is_custom_id=False):
        """ 
        Gets an algo order given order id  (Trigger Order, Stop Loss or Take Profit ) 
        """
        params = {}
        if is_custom_id:
            params['clientOrderId'] = order_id
        if self.exchange_id == 'binance':
            order = self.ccxt.fetchOrder(order_id, symbol, params)
        elif self.exchange_id == 'okex':
            data = self.ccxt.spotGetAlgo(
                {
                    'instrument_id' : symbol.replace('/', '-'), 
                    'order_type' : order_type, 
                    'algo_id': order_id
                })
            order = [next(iter(data))][0]
        else:
            raise NotImplementedError('Getting algo orders not implemented for {}'.format(self.exchange_id))
        # print('Getting order for {} returned'.format(self.exchange_id))
        # pprint(data)
        return order


    def updateSQLOrderModel(self, order, order_response, bot):
        """ 
        Updates an order based on it's state on the exchange given by 
        order_response. Should be part of the exchange interface  """
        # print("Order response is")
        # pprint(order_response)
        if order.is_test:
            if order.side == 'buy':
                order.entry_price = order.price
            if order_response['filled'] is not None:
                order.executed_quantity =  Decimal(order_response['filled'])
            if order_response['status'] is not None:
                order.status = order_response['status']
            if order_response['side'] is not None:
                order.side = order_response['side']
        if not order.is_test:
            if order_response['timestamp'] is not None:
                order.timestamp = datetime.fromtimestamp(
                    order_response['timestamp'] / 1000)
            if order_response['price'] is not None:
                order.price = order_response['price']
                if order.side == 'buy':
                    order.entry_price = order_response['price']
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
        return order


    def getOrderBook(self, symbol, limit):
        if self.exchange_id == 'binance':
            url = 'https://api.binance.com' + '/api/v3/depth' \
                + "?&symbol=" + str(symbol.replace('/', '')) + "&limit=" + str(limit)
            response = requests.get(url)
            payload = json.loads(response.text)
            return payload
        else: 
            raise NotImplementedError
            