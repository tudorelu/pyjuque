import requests
import json
import hashlib
import hmac
import time
import pandas
from decimal import Context, Decimal, getcontext
from traceback import print_exc
import math

import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from os.path import join, dirname

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from datetime import datetime

from pyjuque.Exchanges.Base.Exceptions import \
    InvalidCredentialsException, \
    InternalExchangeException, \
    ExchangeConnectionException

from pprint import pprint
from enum import Enum

class Binance():
    """ Wrapper around the Binance REST API """

    ORDER_STATUS_NEW = 'NEW'
    ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    ORDER_STATUS_FILLED = 'FILLED'
    ORDER_STATUS_CANCELED = 'CANCELED'
    ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL' # NOT USED BY BINANCE ATM
    ORDER_STATUS_REJECTED = 'REJECTED'
    ORDER_STATUS_EXPIRED = 'EXPIRED'

    ORDER_SIDE_BUY = 'BUY'
    ORDER_SIDE_SELL = 'SELL'

    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

    KLINE_INTERVALS = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']

    BASE_URL = 'https://api.binance.com'
    
    ENDPOINTS = {
        "order": '/api/v3/order',
        "testOrder": '/api/v3/order/test',
        "allOrders": '/api/v3/allOrders',
        "klines": '/api/v3/klines',
        "exchangeInfo": '/api/v3/exchangeInfo',
        "averagePrice" : '/api/v3/avgPrice',
        "orderBook" : '/api/v3/depth',
        "account" : '/api/v3/account',
        "ticker": '/api/v3/ticker/bookTicker',
        "tickprice": '/api/v3/ticker/24hr'
    }

    SYMBOL_DATAS = dict()
    TICKER_DATA = dict()
    TICKER_UPDATE_TIME = None

    def __init__(self, filename=None, api_key=None, secret_key=None, get_credentials_from_env=False):
        
        self.api_keys = None
        self.has_credentials = False

        self.updateSymbolsData()
        self.updateTickerData()

        if get_credentials_from_env:
            env_api_key = os.getenv('BINANCE_API_KEY')
            env_secret_key = os.getenv('BINANCE_API_SECRET')
            if env_api_key is not None and env_secret_key is not None:
                self.addCredentials(env_api_key, env_secret_key)
        else:
            if filename is not None:
                file = open(filename, "r")
                if file.mode == 'r':
                    contents = file.read().split('\n')
                    self.addCredentials(api_key = contents[0], secret_key=contents[1])
                else:
                    raise Exception("Can't read", filename, "make sure the file is readable!")
        
        # Adding credentials FROM API & SECRET KEYS passed through init
        if self.has_credentials is False:
            if api_key is not None and secret_key is not None:
                self.addCredentials(api_key, secret_key)

        self.headers = dict()
        # Adding required Headers if credentials exist
        if self.has_credentials:
            self.headers["X-MBX-APIKEY"] = self.api_keys['api_key']

    def _get(self, url, params=None, headers=None):
        """ Implements a get request for this exchange """
        try:
            response = requests.get(url, params=params, headers=headers)
            payload = json.loads(response.text)
            if type(payload) == type([]):
                data = dict(payload=payload, url=url)
            else:
                data = payload
                data['url'] = url

        except requests.exceptions.ConnectionError:
            raise ExchangeConnectionException()
        except Exception as e:
            print("Exception occured when trying to GET from "+url)
            print_exc()
            data = {'code': '-1', 'url':url, 'msg': e}
            # raise ExchangeConnectionException()
        return data

    def _post(self, url, params=None, headers=None):
        """ Implements a post request for this exchange """
        try: 
            response = requests.post(url, params=params, headers=headers)
            data = json.loads(response.text)
            data['url'] = url
        except Exception as e:
            print("Exception occured when trying to POST to "+url); print(e); print("Params"); print(params)
            print_exc()
            data = {'code': '-1', 'url':url, 'msg': e}
        return data

    def _delete(self, url, params=None, headers=None):
        """ Implements a delete request for this exchange """
        try: 
            response = requests.delete(url, params=params, headers=headers)
            data = json.loads(response.text)
            data['url'] = url
        except Exception as e:
            print("Exception occured when trying to DELETE from "+url); print(e); print("Params"); print(params)
            print_exc()
            data = {'code': '-1', 'url':url, 'msg': e, 'params':params}
        return data

    def _signRequest(self, params):
        """ Signs a request with the API & SECRET keys """
        query_string = '&'.join(["{}={}".format(d, params[d]) for d in params])
        signature = hmac.new(self.api_keys['secret_key'].encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        params['signature'] = signature.hexdigest()

    def _getSymbolsData(self):
        """ Gets All symbols' data from Binance """
        url = Binance.BASE_URL + Binance.ENDPOINTS["exchangeInfo"]
        data = self._get(url)
        if not Binance.isValidResponse(data):
            return []

        symbols_list = []
        for pair in data['symbols']:
            symbols_list.append(pair)

        return symbols_list

    def updateSymbolsData(self):
        symbols = self._getSymbolsData()
        for symb in symbols:
            Binance.SYMBOL_DATAS[symb['symbol']] = symb

    def _getTickerData(self):
        """ Gets All symbols' data from Binance """
        url = Binance.BASE_URL + Binance.ENDPOINTS["ticker"]
        data = self._get(url)
        if not Binance.isValidResponse(data):
            return []
        
        symbols_list = []
        for pair in data["payload"]:
            symbols_list.append(pair)

        return symbols_list

    def updateTickerData(self):
        symbols = self._getTickerData()
        self.TICKER_UPDATE_TIME = time.time()
        for symb in symbols:
            Binance.TICKER_DATA[symb["symbol"]] = symb

    def addCredentials(self, api_key, secret_key):
        """ Adds API & SECRET keys into the object's memory """
        new_keys = dict(api_key=api_key, secret_key=secret_key)
        self.api_keys = new_keys
        self.has_credentials = True

    def getCurrentTickPrice(self, symbol):
        url = Binance.BASE_URL + Binance.ENDPOINTS['tickprice']
        params = {'symbol': symbol.upper()}
        tick_info = self._get(url, params, self.headers)
        return tick_info

    def getAccountData(self):
        """ Gets data for Account connected to API & SECRET Keys given """	
        
        url = Binance.BASE_URL + Binance.ENDPOINTS["account"]
        params = {
        'recvWindow': 5000,
        'timestamp': int(round(time.time()*1000))
        }
        self._signRequest(params)
        return self._get(url, params, self.headers)

    def getTradingSymbols(self, quote_assets:list=None):
        """ Gets All symbols which are tradable (currently) 
            Params
            --
                `quote_assets`
                    a list of all the quote assets we are interested in;
                    if empty or None, we will return all trading pairs, 
                    indifferent of quote asset
            Returns
            --
                a list of symbols that are currently trading on Binance 
        """
        url = Binance.BASE_URL + Binance.ENDPOINTS["exchangeInfo"]
        data = self._get(url)
        if not Binance.isValidResponse(data):
            raise ExchangeConnectionException()

        symbols_list = []
        if quote_assets != None and len(quote_assets) > 0:
            for pair in data['symbols']:
                if pair['status'] == 'TRADING':
                    if pair['quoteAsset'] in quote_assets:
                        symbols_list.append(pair['symbol'])
        else:
            for pair in data['symbols']:
                if pair['status'] == 'TRADING':
                    symbols_list.append(pair['symbol'])

        return symbols_list

    def _getPriceInBTCDirectly(self, asset:str):
        """ Returns the price of an `asset` that is traded with BTC as quote or base asset. """
        price_in_btc = None
        getcontext().prec = 28
        if asset == 'BTC':
            price_in_btc = Decimal(1)

        elif self.TICKER_DATA.__contains__(asset+"BTC"):
            ticker_data = self.TICKER_DATA[asset+"BTC"]
            ticker_price = Decimal(0.5) * \
                (Decimal(ticker_data['askPrice']) + Decimal(ticker_data['bidPrice']))
            price_in_btc = ticker_price
            if ticker_price == 0:
                price_in_btc = None
            else:
                price_in_btc = ticker_price

        elif self.TICKER_DATA.__contains__("BTC"+asset):
            ticker_data = self.TICKER_DATA["BTC"+asset]
            ticker_price = Decimal(0.5) * \
                (Decimal(ticker_data['askPrice']) + Decimal(ticker_data['bidPrice']))
            if ticker_price == 0:
                price_in_btc = None
            else:
                price_in_btc = Decimal(1) / ticker_price

        return price_in_btc

    def getPriceInBTC(self, asset:str):
        """ Returns the price of an 'asset', uses triangulation to determine BTC price if needed."""
        possible_pairs = dict()
        price_in_btc = None
        findBTCDirectly = False
        getcontext().prec = 28
        # loop through all pairs to see if asset is traded with BTC as quote or base asset
        for key, value in self.SYMBOL_DATAS.items():
            if asset in key:
                possible_pairs[key] = dict(base=value['baseAsset'], quote=value['quoteAsset'])
                if 'BTC' in key:
                    findBTCDirectly = True

        if findBTCDirectly:
            # asset is traded with BTC as quote or base asset, find price directly.
            price_in_btc = self._getPriceInBTCDirectly(asset)
        elif not findBTCDirectly:
            # asset is not traded with BTC as quote or base asset, use triangulation to find BTC price.
            for pair, quote_base in possible_pairs.items():

                ticker_data = self.TICKER_DATA[pair]
                ticker_price = Decimal(0.5) * \
                (Decimal(ticker_data['askPrice']) + Decimal(ticker_data['bidPrice']))

                if asset == quote_base['base']:
                    price_asset_in_new_asset = ticker_price
                    new_asset = quote_base['quote']
                if asset == quote_base['quote']:
                    price_asset_in_new_asset = Decimal(1) / ticker_price
                    new_asset = quote_base['base']

                btc_price_new_asset = self._getPriceInBTCDirectly(new_asset)

                if btc_price_new_asset is None:
                    # new_asset does not have a quote or base asset in BTC
                    continue
                if btc_price_new_asset is not None:
                    # new_asset does have a quote or base asset in BTC, we can now calculate BTC price!
                    if price_asset_in_new_asset == 0:
                        price_in_btc = None
                    else:
                        price_in_btc = price_asset_in_new_asset * btc_price_new_asset
                        break
        return price_in_btc
    
    def getOrderBook(self, symbol, limit=100):
        """ Gets Order Book data for symbol """

        url = Binance.BASE_URL + Binance.ENDPOINTS["orderBook"]\
            + "?&symbol=" + str(symbol) + "&limit=" + str(limit)
        
        data = self._get(url)

        if not Binance.isValidResponse(data):
            print(data)
            raise Exception(data['msg'])

        return data
    
    def getOrderBookAveragePrice(self, symbol, side, quantity, order_book=None):
        #TODO test it
        """ Calculates the average price we would pay / receive per unit of `symbol` 
        if we wanted to trade `quantity` of that `symbol`, based on its order book"""
        
        obl_index = 0	# index of current order_book limit
        order_book_limits = [100, 500, 1000, 5000]	# possible order_book limits
        if order_book is not None:
            order_book = self.getOrderBook(symbol=symbol, limit=order_book_limits[obl_index])

        # print("Initial order book looks like")
        # pprint(order_book)
        order_book_side = order_book['asks'] \
            if side == Binance.ORDER_SIDE_SELL else order_book['bids']

        quantity = Decimal(quantity)
        i, orders, price = 0, [], Decimal(0)
        accounted_for_quantity = Decimal(0)

        qtdif = Decimal(1)
        while accounted_for_quantity < quantity or qtdif > Decimal(0.0001):
            try:
                order = order_book_side[i]
            except IndexError:
                raise InternalExchangeException("There are not enough orders in the Order Book.")
            qty = min(Decimal(order[1]), quantity - accounted_for_quantity)
            price += Decimal(order[0]) * qty
            accounted_for_quantity += qty
            qtdif = abs(Decimal(1) - accounted_for_quantity / quantity)
            i += 1
            if i >= order_book_limits[obl_index] - 1:
                # print("Reached Order Book Limit of ", i, "Try to get some more")
                if obl_index < 3:
                    obl_index += 1
                    order_book = self.getOrderBook(symbol=symbol, limit=order_book_limits[obl_index])
                    # print("Got new order book with limit", order_book_limits[obl_index])
                    order_book_side = order_book['asks'] \
                        if side == Binance.ORDER_SIDE_SELL else order_book['bids']
                    # print(i, len(order_book_side))
                    # print(qtdif)
                else:
                    # print(symbol, side, quantity)
                    raise InternalExchangeException("There are not enough orders in the Order Book.")

        return price / quantity

    def _getSymbolKlinesExtra(self, symbol:str, interval:str, 
    limit:int=1000, end_time=False, cast_to:type=float):
        """ Gets candlestick data for one symbol if more than 1000
        candles are requested (because of the Binance rate limitation
        of only 1000 candles per request, this function cals getSymbolKlines
        as many times it needs to get the desired number of candles)
        Parameters
        --
            Same as getSymbolKlines
        Returns
        --
            Same as getSymbolKlines
        """

        # Basicall, we will be calling the GetSymbolKlines as many times as we need 
        # in order to get all the historical data required (based on the limit parameter)
        # and we'll be merging the results into one long dataframe.
        repeat_rounds = 0
        if limit > 1000:
            repeat_rounds = int(limit/1000)
        initial_limit = limit % 1000
        if initial_limit == 0:
            initial_limit = 1000
        # First, we get the last initial_limit candles, starting at end_time and going
        # backwards (or starting in the present moment, if end_time is False)
        df = self.getOHLCV(
            symbol, interval, limit=initial_limit, end_time=end_time, cast_to=cast_to)
        while repeat_rounds > 0:
            # Then, for every other 1000 candles, we get them, but starting at the beginning
            # of the previously received candles.
            df2 = self.getOHLCV(
                symbol, interval, limit=1000, end_time=df['time'][0], cast_to=cast_to)
            df = df2.append(df, ignore_index = True)
            repeat_rounds = repeat_rounds - 1
        
        return df

    def getOHLCV(self, symbol:str, interval:str, 
    limit:int=1000, end_time:any=False, start_time:any=False, cast_to:type=float):
        """
        Gets candlestick data for one symbol 
        
        Parameters
        --
            symbol str:
                The symbol for which to get the trading data
            interval str:
                The interval on which to get the trading data
                minutes: '1m' '3m' '5m' '15m' '30m' 
                hours: '1h' '2h' '4h' '6h' '8h' '12h'
                days: '1d' '3d' weeks: '1w' months: '1M'
            limit int: 
                The number of data points (candles) to return
            `end_time` bool/int:
                The time of the last candle (if False, uses current time)
            
        Returns
        --
            DataFrame containing OHLCV data.
        """

        if limit > 1000:
            return self._getSymbolKlinesExtra(
                symbol, interval, limit, end_time, cast_to=cast_to)
        
        params = '?&symbol='+symbol+'&interval='+interval+'&limit='+str(limit)
        if end_time:
            params = params + '&endTime=' + str(int(end_time))
        if start_time:
            params = params + '&startTime=' + str(int(start_time))

        url = Binance.BASE_URL + Binance.ENDPOINTS['klines'] + params

        # download data
        try:
            data = requests.get(url)
        except requests.exceptions.ConnectionError:
            raise ExchangeConnectionException()
        dictionary = json.loads(data.text)

        # put in dataframe and clean-up
        df = pandas.DataFrame.from_dict(dictionary)
        df = df.drop(range(6, 12), axis=1)

        # rename columns
        col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
        df.columns = col_names

        # transform values from strings to floats
        for col in col_names:
            df[col] = df[col].astype(cast_to)

        df['date'] = pandas.to_datetime(df['time'] * 1000000, infer_datetime_format=True)

        return df

    def placeOrder(self, params, test:bool=False, verbose = True):
        """ Places order on exchange given a dictionary of parameters.
            Check this link for more info on the required parameters: 
            https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#new-order--trade
            Parameters
            --
                params dict:
                    A dictionary of parameters containing info about the order,
                    such as SIDE (buy/sell), TYPE (market/limit/oco), SYMBOL, etc.
                test bool:
                    Decides whether this will be a test order or not.
        """

        params['symbol'] = params['symbol'].upper()

        self._signRequest(params)
        
        if verbose:
            print("\n\nPlacing Order with params:")
            pprint(params)
            print("\n")
        url = Binance.BASE_URL + Binance.ENDPOINTS['order']
        if test: 
            url = Binance.BASE_URL + Binance.ENDPOINTS['testOrder']

        return self._post(url, params, self.headers)

    def placeMarketOrder(self, symbol:str, side:str, amount:str, quote_amount=None, 
    test:bool=False, round_up_amount=False, custom_id=False, verbose=False):
        """ Places side (buy/sell) market order for amount of symbol.	"""
        if verbose:
            print("Placing MarketOrder with params:")
        
        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_MARKET,
            'recvWindow': 5000,
            'timestamp': int(round(time.time()*1000))
        }

        if custom_id is not False:
            params['newClientOrderId'] = custom_id

        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, 
                                                                        amount, round_up_amount), 'f')
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')
        if verbose:
            pprint(params)
            
        return self.placeOrder(params, test)

    def placeLimitOrder(self, symbol:str, price, side:str, amount, 
    quote_amount=None, test:bool=False, round_up_price=False, time_in_force=None,
    round_up_amount=False, custom_id=False, verbose=False):
        """ Places side (buy/sell) limit order for amount of symbol at price. """
        if verbose:
            print("Placing LimitOrder with params:")
        
        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_LIMIT,
            'recvWindow': 5000,
            'timeInForce': 'GTC',
            'price': format(self.toValidPrice(symbol, price, round_up_price), 'f'),
            'timestamp': int(round(time.time()*1000))
        }
                
        if custom_id is not False:
            params['newClientOrderId'] = custom_id
                
        if time_in_force in ['GTC', 'IOC', 'FOK']:
            params['timeInForce'] = time_in_force

        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, 
                                                                        amount, round_up_amount), 'f')
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')
        if verbose:
            pprint(params)
        return self.placeOrder(params, test)

    def placeStopLossMarketOrder(self, symbol:str, price, side:str,  amount, 
    quote_amount=None, test:bool=False, round_up_price=False, round_up_amount=False, 
    custom_id=False, verbose=False):
        """ Places a STOP_LOSS market order for amount of symbol at price. """
        if verbose:
            print("Placing StopLossMarketOrder with params:")

        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_STOP_LOSS,
            'recvWindow': 5000,
            'stopPrice': format(self.toValidPrice(symbol, price, round_up_price), 'f'),
            'timestamp': int(round(time.time()*1000))
        }
                
        if custom_id is not False:
            params['newClientOrderId'] = custom_id
            
        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, amount, round_up_amount), 'f')
        
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')

        if verbose:
            pprint(params)

        return self.placeOrder(params, test)

    def placeStopLossLimitOrder(self, symbol:str, price, stop_price, side:str, amount, quote_amount=None, 
    test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=False):
        """ Places a STOP_LOSS_LIMIT market order for amount of symbol at price. """
        if verbose:
            print("Placing StopLossLimitOrder with params:")

        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_STOP_LOSS_LIMIT,
            'recvWindow': 5000,
            'timeInForce': 'GTC',
            'price': format(self.toValidPrice(symbol, price, round_up_price), 'f'),
            'stopPrice': format(self.toValidPrice(symbol, stop_price, round_up_price), 'f'),
            'timestamp': int(round(time.time()*1000))
        }
                
        if custom_id is not False:
            params['newClientOrderId'] = custom_id
                
        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, 
                                                                        amount, round_up_amount), 'f')
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')

        if verbose:
            pprint(params)

        return self.placeOrder(params, test)

    def placeTakeProfitMarketOrder(self, symbol:str, price, side:str, amount, quote_amount=None, 
    test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=False):
        """ Places a TAKE_PROFIT market order for amount of symbol at price. """
        if verbose:
            print("Placing TakeProfitMarketOrder with params:")
        
        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_TAKE_PROFIT,
            'recvWindow': 5000,
            'stopPrice': format(self.toValidPrice(symbol, price, round_up_price), 'f'),
            'timestamp': int(round(time.time()*1000))
        }
                
        if custom_id is not False:
            params['newClientOrderId'] = custom_id
                
        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, amount, round_up_amount), 'f')
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')

        if verbose:
            pprint(params)

        return self.placeOrder(params, test)

    def placeTakeProfitLimitOrder(self, symbol:str, price, stop_price, side:str, amount, quote_amount=None, 
    test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=False):
        """ Places a TAKE_PROFIT_LIMIT order for amount of symbol at price. """
        
        if verbose:
            print("Placing TakeProfitLimitOrder with params:")
            
        params = {
            'symbol': symbol.upper(),
            'side': side,
            'type': Binance.ORDER_TYPE_TAKE_PROFIT_LIMIT,
            'recvWindow': 5000,
            'timeInForce': 'GTC',
            'price': format(self.toValidPrice(symbol, price, round_up_price), 'f'),
            'stopPrice': format(self.toValidPrice(symbol, stop_price, round_up_price), 'f'),
            'timestamp': int(round(time.time()*1000))
        }
                
        if custom_id is not False:
            params['newClientOrderId'] = custom_id
                
        if amount is not None:
            params['quantity'] = format(self.toValidQuantity(symbol, 
                                                                        amount, round_up_amount), 'f')
        elif quote_amount is not None:
            params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
                                                                quote_amount, round_up_amount), 'f')

        if verbose:
            pprint(params)

        return self.placeOrder(params, test)

    def cancelOrder(self, symbol, order_id, is_custom_id=False):
        """ Cancels order given order id """
        params = {
            'symbol': symbol.upper(),
            'recvWindow': 5000,
            'timestamp': int(round(time.time()*1000)) 
        }
        if is_custom_id:
            params['origClientOrderId'] = order_id
        else:
            params['orderId'] = order_id

        self._signRequest(params)
        url = Binance.BASE_URL + Binance.ENDPOINTS['order']
        return self._delete(url, params, self.headers)

    def getOrder(self, symbol, order_id, is_custom_id=True):
        """ Gets order info given order id """
        params = {
            'symbol': symbol.upper(),
            'recvWindow': 5000,
            'timestamp': int(round(time.time()*1000)) 
        }
        if is_custom_id:
            params['origClientOrderId'] = order_id
        else:
            params['orderId'] = order_id
        print(params)
        self._signRequest(params)
        url = Binance.BASE_URL + Binance.ENDPOINTS['order']
        return self._get(url, params, self.headers)

    def getAllOrders(self, symbol, limit=500):
        """ Gets order info given order id """
        params = {
            'symbol': symbol.upper(),
            'limit': limit,
            'timestamp': int(round(time.time()*1000)) 
        }
        self._signRequest(params)
        url = Binance.BASE_URL + Binance.ENDPOINTS['allOrders']
        return self._get(url, params, self.headers)

    @classmethod
    def isValidResponse(cls, response:dict):
        """ 
        Checks whether response received from exchange is valid
        Returns 
        --
        True if valid, False otherwise
        """
        return not response.__contains__('code')

    @classmethod
    def floatToString(cls, f:float):
        ''' Converts the given float to a string,
        without resorting to the scientific notation '''

        ctx = Context()
        ctx.prec = 32
        d1 = ctx.create_decimal(repr(f))
        return format(d1, 'f')

    @classmethod
    def _get10Factor(cls, num):
        """ Returns the power of 10 with which this number needs to be multiplied 
        so that it's between 1 (inclusive) and 10 (exclusive)
        
        _get10Factor(0.00000164763) = 6
        _get10Factor(1600623.3) = -6
        """
        p = 0
        for i in range(-20, 20):
            if num == num % 10**i:
                p = -(i - 1)
                break
        return p

    @classmethod
    def _round_down_decimals(cls, number, decimals):
        factor = 10 ** decimals
        return math.floor(Decimal(number) * Decimal(factor)) / Decimal(factor)

    def toValidPrice(self, symbol, desired_price, round_up:bool=False) \
        -> Decimal():
        """ Returns the minimum quantity of a symbol we can buy, 
        closest to desiredPrice """
        
        pr_filter = {}
        symbol = symbol.upper()

        if not self.SYMBOL_DATAS.__contains__(symbol):
            self.updateSymbolsData()
            if not self.SYMBOL_DATAS.__contains__(symbol):
                raise InternalExchangeException(\
                    "Could not find symbol data of "+symbol)

        for fil in self.SYMBOL_DATAS[symbol]["filters"]:
            if fil["filterType"] == "PRICE_FILTER":
                pr_filter = fil
                break
        
        if not pr_filter.keys().__contains__("tickSize"):
            raise InternalExchangeException(\
                "Couldn't find tickSize or PRICE_FILTER in symbol_data.")

        round_off_by = int(Binance._get10Factor((float(pr_filter["tickSize"]))))
        number = round(Decimal(desired_price), round_off_by)
        if round_up:
            number = number + Decimal(pr_filter["tickSize"])

        return number

    def toValidQuantity(self, symbol, desired_quantity, round_up:bool=False) \
        -> Decimal():
        """ Returns the minimum quantity of a symbol we can buy,
        closest to desiredPrice """
        
        lot_filter = {}

        symbol = symbol.upper()
        # Check whether SD exists
        if not self.SYMBOL_DATAS.__contains__(symbol):
            self.updateSymbolsData()
            if not self.SYMBOL_DATAS.__contains__(symbol):
                raise InternalExchangeException(\
                    "Could not find symbol data of "+symbol)

        # Check the LOT SIZE filter on SD
        for fil in self.SYMBOL_DATAS[symbol]["filters"]:
            if fil["filterType"] == "LOT_SIZE":
                lot_filter = fil
                break
        
        if not lot_filter.keys().__contains__("stepSize"):
            raise InternalExchangeException(\
                "Couldn't find stepSize or PRICE_FILTER in symbol_data.")

        decimals = int(self._get10Factor((float(lot_filter["stepSize"]))))
        quantity = self._round_down_decimals(number = desired_quantity, decimals = decimals)
        if round_up:
            quantity = quantity + Decimal(lot_filter["stepSize"])

        return quantity

    def updateSQLOrderModel(self, order, new_order_response, bot):
        """ Updates an order based on it's state on the exchange given by 
        new_order_response. Should be part of the exchange interface  """

        if order.is_test:
            if order.side == 'BUY':
                order.entry_price = order.price
            
        if not order.is_test:
            if new_order_response.__contains__('transactTime'):
                order.timestamp = datetime.fromtimestamp(
                    new_order_response['transactTime']/1000)
            else:
                order.timestamp = datetime.fromtimestamp(
                    new_order_response['time']/1000)
            # pprint(new_order_response)
            order.price = new_order_response['price']
            order.original_quantity =  Decimal(new_order_response['origQty'])
            order.executed_quantity =  Decimal(new_order_response['executedQty'])
            order.status = new_order_response['status']
            order.side = new_order_response['side']
            order.order_type = new_order_response['type']
            if order.side == 'BUY':
                order.entry_price = new_order_response['price']

        return order
