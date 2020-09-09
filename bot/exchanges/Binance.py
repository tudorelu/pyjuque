import requests
import json
import hashlib
import hmac
import time
import pandas
from decimal import Context, Decimal
from traceback import print_exc
import math

# TODO some code is repeating below here, rewrite this
import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)
from os.path import join, dirname
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '../../.env'))
# END TODO

from bot.Exchanges.Base.BaseExchange import BaseExchange # pylint: disable=E0401
from bot.Exchanges.Base.Exceptions import InvalidCredentialsException, InternalExchangeException, ExchangeConnectionException # pylint: disable=E0401

from pprint import pprint

class Binance(BaseExchange):

	ORDER_STATUS_NEW = 'NEW'
	ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
	ORDER_STATUS_FILLED = 'FILLED'
	ORDER_STATUS_CANCELED = 'CANCELED'
	ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL' # NOT USED BY BINANCE ATM
	ORDER_STATUS_REJECTED = 'REJECTED'
	ORDER_STATUS_EXPIRED = 'EXPIRED'

	SIDE_BUY = 'BUY'
	SIDE_SELL = 'SELL'

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
		"account" : '/api/v3/account'
	}

	SYMBOL_DATAS = dict()

	def __init__(self, filename=None, api_key=None, secret_key=None, get_credentials_from_env=False):
		
		self.api_keys = None
		self.has_credentials = False

		self._updateSymbolsData()

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
		except Exception as e:
			print("Exception occured when trying to GET from "+url)
			print_exc()
			data = {'code': '-1', 'url':url, 'msg': e}
		return data

	def _post(self, url, params=None, headers=None,):
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

	def _updateSymbolsData(self):
		symbols = self._getSymbolsData()
		for symb in symbols:
			Binance.SYMBOL_DATAS[symb['symbol']] = symb

	def addCredentials(self, api_key, secret_key):
		""" Adds API & SECRET keys into the object's memory """
		new_keys = dict(api_key=api_key, secret_key=secret_key)
		self.api_keys = new_keys
		self.has_credentials = True

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

	def getOrderBookData(self, symbol):
		""" Gets Order Book data for symbol """
		return None
	
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
		df = self.getSymbolKlines(
			symbol, interval, limit=initial_limit, end_time=end_time, cast_to=cast_to)
		while repeat_rounds > 0:
			# Then, for every other 1000 candles, we get them, but starting at the beginning
			# of the previously received candles.
			df2 = self.getSymbolKlines(
				symbol, interval, limit=1000, end_time=df['time'][0], cast_to=cast_to)
			df = df2.append(df, ignore_index = True)
			repeat_rounds = repeat_rounds - 1
		
		return df

	def getSymbolKlines(self, symbol:str, interval:str, 
	limit:int=1000, end_time:any=False, cast_to:type=float):
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

		url = Binance.BASE_URL + Binance.ENDPOINTS['klines'] + params

		# download data
		data = requests.get(url)
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
			print("Placing Order with params:")
			pprint(params)
		
		url = Binance.BASE_URL + Binance.ENDPOINTS['order']
		if test: 
			url = Binance.BASE_URL + Binance.ENDPOINTS['testOrder']

		return self._post(url, params, self.headers)

	def placeMarketOrder(self, symbol:str, side:str, amount:str, quote_amount=None, 
	test:bool=False, round_up_amount=False, custom_id=False, verbose=True):
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

	def placeLimitOrder(self, symbol:str, price, side:str, amount, quote_amount=None, 
	test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=True):
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
				
		if amount is not None:
			params['quantity'] = format(self.toValidQuantity(symbol, 
																		amount, round_up_amount), 'f')
		elif quote_amount is not None:
			params['quoteOrderQty'] = format(self.toValidQuantity(symbol, 
																quote_amount, round_up_amount), 'f')
		if verbose:
			pprint(params)
		return self.placeOrder(params, test)

	def placeStopLossMarketOrder(self, symbol:str, price, side:str,  amount, quote_amount=None, 
	test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=True):
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
	test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=True):
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
	test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=True):
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
	 test:bool=False, round_up_price=False, round_up_amount=False, custom_id=False, verbose=True):
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

	def getOrder(self, symbol, order_id, is_custom_id=False):
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
		return math.floor(number * factor)/factor

	def toValidPrice(self, symbol, desired_price, round_up:bool=False) \
		-> Decimal():
		""" Returns the minimum quantity of a symbol we can buy, 
		closest to desiredPrice """
		
		pr_filter = {}
		symbol = symbol.upper()

		if not self.SYMBOL_DATAS.__contains__(symbol):
			self._updateSymbolsData()
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
			self._updateSymbolsData()
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
			order.take_profit_price = self.toValidPrice(
				symbol = order.symbol,
				desired_price = Decimal(order.entry_price) * (Decimal(100) + Decimal(bot.profit_target))/Decimal(100), 
				round_up=True)

		else:
			order.timestamp = new_order_response['transactTime']
			order.entry_price = new_order_response['price']
			order.take_profit_price = self.toValidPrice(
				symbol = order.symbol,
				desired_price = Decimal(new_order_response['price']) * Decimal(bot.profit_target), 
				round_up=True)
			order.original_quantity =  Decimal(new_order_response['origQty'])
			order.executed_quantity =  Decimal(new_order_response['executedQty'])
			order.status = new_order_response['status']
			order.side = new_order_response['side']

		return order
