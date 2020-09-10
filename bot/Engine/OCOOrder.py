from uuid import uuid4
from pprint import pprint
from bot.Exchanges.Binance import Binance
import json, websocket, numpy
from decimal import Decimal

#	Entry Order - Simple Limit Order
#	Exit Order - Complex OCO Order
#	For OCO Order, the market needs to be checked periodically (websockets)
# 	If price approaches SL, We cancel TP Order and place SL
# 	If price approaches TP, we cancel SL Order and place TP

EXCHANGE_INVALID_RESPONSE = "Not a valid response from the exchange, try again next time..."

class OCOOrder:
	ORDER_TYPE_SL = "STOP_LOSS"
	ORDER_TYPE_TP = "TAKE_PROFIT"

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
			self.symbol = symbol
			self.verbose = verbose
			self.quantity = quantity
			self.exchange = exchange
			self.stop_loss = self.exchange.toValidPrice(self.symbol.upper(), stop_loss)
			self.take_profit = self.exchange.toValidPrice(self.symbol.upper(), take_profit)

			self.is_order_closed = False
			self.is_order_placed = False
			self.current_order_id = None
			self.current_order_type = None
			self.is_order_profitable = False
			
			self.tp_sl_diff = self.exchange.toValidPrice(self.symbol.upper(), (self.take_profit - self.stop_loss))
			
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
			printable_price = self.exchange.toValidPrice(self.symbol.upper(), price)
			print("Price {}, stop loss {}, take profit {}, sl_tp_diff {}!".format(
				printable_price, 
				self.stop_loss, 
				self.take_profit, 
				self.tp_sl_diff))

		if price <= self.stop_loss:
			# Stop Loss was hit 
			if self.verbose > 0:
				print("Stop Loss was hit!!")

			# An order was not placed before. Place a Market Order to exit trade (at a loss).
			order_id = uuid4()
			new_order = self.exchange.placeMarketOrder(
				symbol=self.symbol, 
				amount=self.quantity, 
				side="SELL", 
				custom_id=order_id,
				verbose=self.verbose)
			
			if self.verbose > 1:
				print("An order was not placed before. Place a Market Order (at a loss)")
				pprint(new_order)
			
			if self.exchange.isValidResponse(new_order):
				self.current_order_id = order_id
				self.current_order_type = self.ORDER_TYPE_SL
				self.is_order_placed = True
				if self.verbose > 1:
					print("Success placing Market order! New Order Id", self.current_order_id)
			else:
				if self.verbose > 1:
					print(EXCHANGE_INVALID_RESPONSE)
				
		elif price >= self.take_profit:
			# Take Profit Target was hit! Check if an order was placed before
			if self.verbose > 0:
				print("Take Profit was hit!!")
			
			# An order was not placed before. Place a Market Order to exit trade (for profit).
			order_id = uuid4()
			new_order = self.exchange.placeMarketOrder(
				symbol=self.symbol, 
				amount=self.quantity, 
				side="SELL", 
				custom_id=order_id,
				verbose=self.verbose)

			if self.verbose > 1:
				print("An order was not placed before. Place a Market Order (for profit)")
				pprint(new_order)
		
			if self.exchange.isValidResponse(new_order):
				self.current_order_id = order_id
				self.current_order_type = self.ORDER_TYPE_SL
				self.is_order_placed = True
				if self.verbose > 1:
					print("Success placing Market order! New Order Id:", self.current_order_id)
			else:
				if self.verbose > 1:
					print(EXCHANGE_INVALID_RESPONSE)
		
		if self.is_order_placed:
			current_order_info = self.get_current_order_info()
			if self.verbose > 0 and current_order_info:
				print("Information of current order:")
				pprint(current_order_info)

			if current_order_info is not False:
				if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
					if self.verbose > 0:
						print("Order was filled so OCO is officially CLOSED!")
					self.is_order_closed = True
					if self.current_order_type == self.ORDER_TYPE_SL:
						self.is_order_profitable = False
					else:
						self.is_order_profitable = True
				else:
					if self.verbose > 0:
						print("Waiting for order to fill, " +
						"current status: {}".format(current_order_info['status']))


		if self.verbose > 0:
			if self.is_order_closed:
				if self.is_order_profitable:
					print("YAY! OCO order was profitable :D")
				else:
					print("NOO! OCO order was not profitable :(")
				print("Closing down this websocket.")
				self.ws.close()

			print("End message...\n")

	def get_current_order_info(self):
		order_info = self.exchange.getOrder(self.symbol, self.current_order_id, is_custom_id=True)
		if self.exchange.isValidResponse(order_info):
			return order_info

		return False
		