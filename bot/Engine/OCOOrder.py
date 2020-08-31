
from uuid import uuid4
from pprint import pprint
from bot.Exchanges.Binance import Binance
import json, websocket, numpy
#	Entry Order - Simple Limit Order
#	Exit Order - Complex OCO Order
#	For OCO Order, the market needs to be checked periodically (websockets)
# 	If price approaches SL, We cancel TP Order and place SL
# 	If price approaches TP, we cancel SL Order and place TP

class OCOOrder:
	ORDER_TYPE_SL = "STOP_LOSS"
	ORDER_TYPE_TP = "TAKE_PROFIT"

	def __init__(self, exchange=None, symbol=None, quantity=None, side=None, stop_loss=None, take_profit=None):
			""" Places an OCO Order on `exchange` """
			self.symbol = symbol
			self.quantity = quantity
			self.exchange = exchange
			self.stop_loss = stop_loss
			self.take_profit = take_profit

			self.is_order_closed = False
			self.is_order_placed = False
			self.current_order_id = None
			self.current_order_type = None
			self.is_order_profitable = False
			
			self.tp_sl_diff = take_profit - stop_loss

			SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
			self.ws = websocket.WebSocketApp(SOCKET, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)
			self.ws.run_forever()

	def on_open(self):
			print('opened connection')

	def on_close(self):
			print('closed connection')

	def on_message(self, message):
			
			print('received message')
			json_message = json.loads(message)
			pprint(json_message)
			candle = json_message['k']
			price = candle['c']

			if price <= self.stop_loss:
				# Stop Loss was hit
				if self.is_order_placed:
					# An order was already placed before, what type was it?
					if self.current_order_id == self.ORDER_TYPE_SL:
						# Stop Loss order was placed before.
						# Check order with exchange to see if it was filled.
						order_info = self.exchange.getOrder(self.symbol, self.current_order_id)
						if self.exchange.isValidResponse(order_info):
  						# TODO Make such that we get an exchange Order object instead of a dict
							if order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								self.is_order_closed = True
								self.is_order_profitable = False 

					elif self.current_order_id == self.ORDER_TYPE_TP:
						# Stop loss was hit, although take profit order was placed.
						# Cancel TP Order and place market order to exit trade (at a loss).
						order_info = self.exchange.getOrder(self.symbol, self.current_order_id)
						if self.exchange.isValidResponse(order_info):
							# CHECK STATUS OF TP ORDER
							if order_info['status'] in [self.exchange.ORDER_STATUS_NEW, \
								self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
  							# If not filled, cancel it
								cancel_order_info = self.exchange.cancelOrder(self.symbol, self.current_order_id)
								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										quantity = self.quantity - order_info['executedQty']
									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, amount=quantity, side="SELL", custom_id=order_id)
									if self.exchange.isValidResponse(new_order):
										self.current_order_id = order_id
										self.current_order_type = self.ORDER_TYPE_SL
										self.is_order_placed = True

							elif order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								self.is_order_closed = True
								self.is_order_profitable = True 
						
				else:
					# An order was not placed before. Place a Market Order (at a loss)
					order_id = uuid4()
					new_order = self.exchange.placeMarketOrder(
						symbol=self.symbol, amount=self.quantity, side="SELL", custom_id=order_id)
					if self.exchange.isValidResponse(new_order):
						self.current_order_id = order_id
						self.current_order_type = self.ORDER_TYPE_SL
						self.is_order_placed = True
			elif price >= self.take_profit:
				# Take Profit Target was hit! Check if an order was placed before
				if self.is_order_placed:
					# Order was placed before, check what type it was
					if self.current_order_id == self.ORDER_TYPE_SL:
						# TP was hit, although stop loss order was placed.
						# Cancel SL Order and place market order (at a profit).
						order_info = self.exchange.getOrder(self.symbol, self.current_order_id)
						if self.exchange.isValidResponse(order_info):
							# CHECK STATUS OF TP ORDER
							if order_info['status'] in [self.exchange.ORDER_STATUS_NEW, \
								self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
  							# If not filled, cancel it
								cancel_order_info = self.exchange.cancelOrder(self.symbol, self.current_order_id)
								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										quantity = self.quantity - order_info['executedQty']
									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, amount=quantity, side="SELL", custom_id=order_id)
									if self.exchange.isValidResponse(new_order):
										self.current_order_id = order_id
										self.current_order_type = self.ORDER_TYPE_SL
										self.is_order_placed = True

							elif order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								self.is_order_closed = True
								self.is_order_profitable = False 

					elif self.current_order_id == self.ORDER_TYPE_TP:
						# Check order with exchange to see if it was filled
						# If it was, close connection, order was complete!
						order_info = self.exchange.getOrder(self.symbol, self.current_order_id)
						if self.exchange.isValidResponse(order_info):
  						# TODO Make such that we get an exchange Order object instead of a dict
							if order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								self.is_order_closed = True
								self.is_order_profitable = True 
				else:
					# An order was not placed before. Place a Market Order to exit trade (for profit).
					order_id = uuid4()
					new_order = self.exchange.placeMarketOrder(
						symbol=self.symbol, amount=self.quantity, side="SELL", custom_id=order_id)
					if self.exchange.isValidResponse(new_order):
						self.current_order_id = order_id
						self.current_order_type = self.ORDER_TYPE_SL
						self.is_order_placed = True
			else:
				# Current price is between take profit and stop loss prices.
				if self.stop_loss < price <= self.stop_loss + self.tp_sl_diff * 0.33:
					#	Price is within 1/3 distance of Stop Loss, we should have a stop loss order placed.
					if self.is_order_placed:
						# There's an order already placed. Is it the right one?
						if self.current_order_type == self.ORDER_TYPE_SL:
							# We have the right order placed, do nothing.
							pass
						elif self.current_order_type == self.ORDER_TYPE_TP:
							# We don't have the right order placed, cancel current order and place a new one.
							if self.current_order_id == None:
								raise Exception("current_order_id is None despite an order appearing to be placed.")
							cancel_response = self.exchange.cancelOrder(self.symbol, self.current_order_id)
							if self.exchange.isValidResponse(cancel_response):
								# TODO: (Make use of DB persistency, get order_id from DB)
								self.current_order_id = None
								self.current_order_type = None
								order_id = uuid4()
								response = self.exchange.placeStopLossMarketOrder(
									symbol=self.symbol, quantity=self.quantity, side=self.side, 
									price=self.stop_loss, custom_order_id=order_id)
								if self.exchange.isValidResponse(response):
									self.current_order_id = order_id
									self.current_order_type = self.ORDER_TYPE_SL
							else:
  							# Unable to cancel order. Try again next time.
								pass
							
						else:
							# There's a problem, throw an exception.
							raise Exception("It seems like there's an order placed, but it's neither SL nor TP.")
					else:
						# There's no order placed. Need to place a SL Order. 
						# TODO: (Make use of DB persistency, get order_id from DB)
						order_id = uuid4()
						response = self.exchange.placeStopLossMarketOrder(symbol=self.symbol, quantity=self.quantity, 
							side=self.side, price=self.stop_loss, custom_order_id=order_id)
						if self.exchange.isValidResponse(response):
							self.current_order_id = order_id
							self.current_order_type = self.ORDER_TYPE_SL
				elif self.stop_loss + self.tp_sl_diff * 0.33 <= price <= self.stop_loss + self.tp_sl_diff * 0.66:
					#	Price is within 1/3 and 2/3 distance of Stop Loss and Take Profit. Do Nothing.
					pass
				elif self.stop_loss + self.tp_sl_diff * 0.66 <= price < self.take_profit:
					# Price is within 1/3 of take profit, we should have a take profit order placed.
					if self.is_order_placed:
						# There's an order already placed. Is it the right one?
						if self.current_order_type == self.ORDER_TYPE_SL:
							# We don't have the right order placed, cancel current order and place a new one.
							if self.current_order_id == None:
								raise Exception("current_order_id is None despite an order appearing to be placed.")
							cancel_response = self.exchange.cancelOrder(self.symbol, self.current_order_id)
							if self.exchange.isValidResponse(cancel_response):
								# TODO: (Make use of DB persistency, get order_id from DB)
								self.current_order_id = None
								self.current_order_type = None
								order_id = uuid4()
								response = self.exchange.placeTakeProfitMarketOrder(
									symbol=self.symbol, quantity=self.quantity, side=self.side, 
									price=self.take_profit, custom_order_id=order_id)
								if self.exchange.isValidResponse(response):
									self.current_order_id = order_id
									self.current_order_type = self.ORDER_TYPE_TP
							else:
								# There was an error cancelling order from exchange. Try again next time!
								pass
							
						elif self.current_order_type == self.ORDER_TYPE_TP:
							# We have the right order placed, do nothing.
							pass
						else:
							# There's a problem, throw an exception.
							raise Exception("It seems like there's an order placed, but it's neither SL nor TP.")
					else:
						# There's no order placed. Need to place a TP Order. 
						# TODO: (Make use of DB persistency, get order_id from DB)
						order_id = uuid4()
						response = self.exchange.placeTakeProfitMarketOrder(symbol=self.symbol, quantity=self.quantity, 
							side=self.side, price=self.take_profit, custom_order_id=order_id)
						if self.exchange.isValidResponse(response):
							self.current_order_id = order_id
							self.current_order_type = self.ORDER_TYPE_TP


def Main():
	order = OCOOrder()

if __name__ == '__main__':
	Main()