from uuid import uuid4
from pprint import pprint
from bot.Exchanges.Binance import Binance
import json, websocket, numpy
from decimal import Decimal

EXCHANGE_INVALID_MESSAGE = "Not a valid response from the exchange, try again next time..."
CLOSING_WEBSOCKET_MESSAGE = "Closing down this websocket."
ORDER_CLOSED_MESSAGE = "Order was filled so OCO is officially CLOSED!"
ORDER_PROFITABLE_MESSAGE = "YES! OCO order was profitable :D"
ORDER_NOT_PROFITABLE_MESSAGE = "NOO! OCO order was not profitable :("
CURRENT_ORDER_INFO_MESSAGE = "Information of current order"
PLACE_MARKET_ORDER_LOSS_MESSAGE = "Place a Market Order to exit trade at a loss."
PLACE_MARKET_ORDER_PROFIT_MESSAGE = "Place a Market Order to exit trade at a profit."
SL_HIT_MESSAGE = "Stop Loss Price was hit!!"
TP_HIT_MESSAGE = "Take Profit Price was hit!!"
SUCCESS_PLACING_ORDER_MESSAGE = "Success Placing Order!"

ORDER_TYPE_SL = "STOP_LOSS"
ORDER_TYPE_TP = "TAKE_PROFIT"

class OCOOrder:
	"""
		For OCO Order, the market needs to be checked periodically (websockets)
		Simple Version:
		--
			If price crosses `SL_Price` or `TP_Price`, place market order
			
		Complex Version:
		--
			## NOT IMPLEMENTED ##
			If price crosses `SL_Stop`
			  * If there's a TP order placed, cancel it if not filled
			  * Place a Stop Order at `SL_Price` with remaining funds
			If price crosses `TP_Stop`
			  * If there's a SL order placed, cancel it if not filled
			  * Place a Limit Order at `TP_Price` with remaining funds
	"""

	def __init__(self, 
		exchange=None, 
		symbol=None, 
		quantity=None, 
		side=None, 
		stop_loss=None, 
		take_profit=None, 
		verbose=False):
			""" Places an OCO Order on `exchange` """
			self.side = side
			self.symbol = symbol.upper()
			self.verbose = verbose
			self.quantity = quantity
			self.exchange = exchange
			self.stop_loss = self.exchange.toValidPrice(self.symbol, stop_loss)
			self.take_profit = self.exchange.toValidPrice(self.symbol, take_profit)

			self.is_order_closed = False
			self.is_order_placed = False
			self.current_order_id = None
			self.current_order_type = None
			self.is_order_profitable = False
			
			if self.verbose > 0:
				print("Placing an oco order for {} {}, stop loss at {} and take profit at {}".format(
					self.quantity, 
					self.symbol, 
					self.stop_loss, 
					self.take_profit))

	
	def start(self):
		self.socket_url = "wss://stream.binance.com:9443/ws/"+self.symbol.lower()+"@kline_1m"
		self.ws = websocket.WebSocketApp(
			self.socket_url, 
			on_open=self.on_open, 
			on_close=self.on_close, 
			on_message=self.on_message)
		self.ws.run_forever()

	def on_open(self):
		if self.verbose > 0:
			print('Opened connection on', self.symbol)

	def on_close(self):
		if self.verbose > 0:
			print('Closed connection')

	def on_message(self, message):

		json_message = json.loads(message)
		candle = json_message['k']
		price = Decimal(candle['c'])

		if self.verbose > 0:
			printable_price = self.exchange.toValidPrice(self.symbol, price)
			print("Price {}, stop loss {}, take profit {}.".format(
				printable_price, 
				self.stop_loss, 
				self.take_profit))

		if self.is_order_closed:
			self.ws.close()

		if not self.is_order_placed and price <= self.stop_loss:
			# Stop Loss was hit 
			if self.verbose > 0:
				print(SL_HIT_MESSAGE)

			# Place a Market Order to exit trade (at a loss).
			order_id = uuid4()
			new_order = self.exchange.placeMarketOrder(
				symbol=self.symbol, 
				amount=self.quantity, 
				side="SELL", 
				custom_id=order_id,
				verbose=(self.verbose>1))
			
			if self.verbose > 1:
				print(PLACE_MARKET_ORDER_LOSS_MESSAGE)
				pprint(new_order)
			
			if self.exchange.isValidResponse(new_order):
				self.current_order_id = order_id
				self.current_order_type = ORDER_TYPE_SL
				self.is_order_placed = True
				if self.verbose > 1:
					print(SUCCESS_PLACING_ORDER_MESSAGE, 
					" New Order Id is {}".format(self.current_order_id))
			else:
				if self.verbose > 1:
					print(EXCHANGE_INVALID_MESSAGE)
				
		elif not self.is_order_placed and price >= self.take_profit:
			# Take Profit Target was hit! 
			if self.verbose > 0:
				print(TP_HIT_MESSAGE)
			
			# Place a Market Order to exit trade (for profit).
			order_id = uuid4()
			new_order = self.exchange.placeMarketOrder(
				symbol=self.symbol, 
				amount=self.quantity, 
				side="SELL", 
				custom_id=order_id,
				verbose=(self.verbose>1))

			if self.verbose > 1:
				print(PLACE_MARKET_ORDER_PROFIT_MESSAGE)
				pprint(new_order)

			if self.exchange.isValidResponse(new_order):
				self.current_order_id = order_id
				self.current_order_type = ORDER_TYPE_TP
				self.is_order_placed = True
				if self.verbose > 1:
					print(SUCCESS_PLACING_ORDER_MESSAGE, 
					" New Order Id is {}".format(self.current_order_id))
			else:
				if self.verbose > 1:
					print(EXCHANGE_INVALID_MESSAGE)
		
		if self.is_order_placed:
			current_order_info = self.get_current_order_info()
			if current_order_info is not False:
				if self.verbose > 0:
					print(CURRENT_ORDER_INFO_MESSAGE)
					pprint(current_order_info)
				if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
					if self.verbose > 0:
						print(ORDER_CLOSED_MESSAGE)
					self.is_order_closed = True
					if self.current_order_type == ORDER_TYPE_SL:
						self.is_order_profitable = False
					else:
						self.is_order_profitable = True
				else:
					if self.verbose > 0:
						print("Waiting for order to fill, current " +
							"status: {}".format(current_order_info['status']))

		if self.is_order_closed:
			if self.verbose > 0:
				if self.is_order_profitable:
					print(ORDER_PROFITABLE_MESSAGE)
				else:
					print(ORDER_NOT_PROFITABLE_MESSAGE)
				print(CLOSING_WEBSOCKET_MESSAGE)
			self.ws.close()

		if self.verbose > 0:
			print("\n")

	def get_current_order_info(self):
		order_info = self.exchange.getOrder(self.symbol, self.current_order_id, is_custom_id=True)
		if self.exchange.isValidResponse(order_info):
			return order_info

		return False
		