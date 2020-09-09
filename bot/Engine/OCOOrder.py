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

	def __init__(self, exchange=None, symbol=None, quantity=None, side=None, stop_loss=None, take_profit=None):
			""" Places an OCO Order on `exchange` """
			self.side = side
			self.symbol = symbol
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

			self.sl_plus_one_3_diff = self.exchange.toValidPrice(self.symbol.upper(), self.stop_loss + self.tp_sl_diff * Decimal(0.33333333333))
			self.sl_plus_two_3_diff = self.exchange.toValidPrice(self.symbol.upper(), self.stop_loss + self.tp_sl_diff * Decimal(0.66666666666))

			print("Placing an oco order for {} {}, stop loss at {} and take profit at {}".format(self.quantity, self.symbol, self.stop_loss, self.take_profit))

	
	def start(self):
		self.socket_url = "wss://stream.binance.com:9443/ws/"+self.symbol.lower()+"@kline_1m"
		self.ws = websocket.WebSocketApp(self.socket_url, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)
		self.ws.run_forever()

	def on_open(self):
			print('opened connection on', symbol)

	def on_close(self):
			print('closed connection')

	def on_message(self, message):
			
			if self.is_order_closed:
				print("OCO Order is closed!")
				if self.is_order_profitable:
					print("YAY! OCO order was profitable")
				else:
					print("NOO! OCO order was not profitable")
				print("Information of exit order:")
				self.getCurrentOrderInfo()
				print("Closing down this websocket...")
				self.ws.close()
				return

			print("\nStart message...")
			json_message = json.loads(message)
			# pprint(json_message)
			candle = json_message['k']
			price = Decimal(candle['c'])
			printable_price = self.exchange.toValidPrice(self.symbol.upper(), price)
			
			print(r"Price {}, stop loss {}, take profit {}, sl_tp_diff {}!".format(printable_price, self.stop_loss, self.take_profit, self.tp_sl_diff))
			# print(r"Stop loss + 1/3 * sl_tp_diff! {}".format(self.sl_plus_one_3_diff))
			# print(r"Stop loss + 2/3 * sl_tp_diff! {}".format(self.sl_plus_two_3_diff))
			# print(r"Stop loss + sl_tp_diff! {}".format(self.stop_loss + self.tp_sl_diff))

			if price <= self.stop_loss:
				# Stop Loss was hit
				print("Stop Loss was hit!!")
				if self.is_order_placed:
					# An order was already placed before, what type was it?
					if self.current_order_type == self.ORDER_TYPE_SL:
						print("Stop Loss order was placed before.")
						# Stop Loss order was placed before.
						# Check order with exchange to see if it was filled.
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								print("Order was filled so OCO is CLOSED!")
								self.is_order_closed = True
								self.is_order_profitable = False 
							else:
								print("Waiting for order to fill, current status: {}".format(current_order_info['status']))

					elif self.current_order_type == self.ORDER_TYPE_TP:
						# Stop loss was hit, although take profit order was placed.
						# Cancel TP Order and place market order to exit trade (at a loss).
						print("Stop Loss hit but TP was placed before !?")
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							# CHECK STATUS OF TP ORDER
							if current_order_info['status'] in [self.exchange.ORDER_STATUS_NEW, self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
								# If not filled, cancel it
								print("If not filled, cancel it.")
								cancel_order_info = self.exchange.cancelOrder(self.symbol, self.current_order_id, is_custom_id=True)
								pprint(cancel_order_info)
								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if current_order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										sold_percentage = Decimal(current_order_info['executedQty'])/self.quantity
										print("Already sold some for a profit:", sold_percentage, "%", "or", Decimal(current_order_info['executedQty']))
										quantity = self.quantity - Decimal(current_order_info['executedQty'])
									print("Remaining quantity:", quantity, "\nPlacing market order to get rid of this.")
									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, amount=quantity, side="SELL", custom_id=order_id)
									pprint(new_order)
									if self.exchange.isValidResponse(new_order):
										self.current_order_id = order_id
										self.current_order_type = self.ORDER_TYPE_SL
										self.is_order_placed = True
										print("Success placing Market order! New Order Id", self.current_order_id)
									else:
										print(EXCHANGE_INVALID_RESPONSE)

							elif current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								print("TP order filled! Success!")
								self.is_order_closed = True
								self.is_order_profitable = True 		
							else:
								print("Waiting for order to fill, current status: {}".format(current_order_info['status']))	
				else:
					# An order was not placed before. Place a Market Order (at a loss)
					print("An order was not placed before. Place a Market Order (at a loss)")
					order_id = uuid4()
					new_order = self.exchange.placeMarketOrder(
						symbol=self.symbol, amount=self.quantity, side="SELL", custom_id=order_id)
					pprint(new_order)
					if self.exchange.isValidResponse(new_order):
						self.current_order_id = order_id
						self.current_order_type = self.ORDER_TYPE_SL
						self.is_order_placed = True
						print("Success placing Market order! New Order Id", self.current_order_id)
					else:
						print(EXCHANGE_INVALID_RESPONSE)
			elif price >= self.take_profit:
				# Take Profit Target was hit! Check if an order was placed before
				print("Take Profit was hit!!")
				if self.is_order_placed:
					# Order was placed before, check what type it was
					if self.current_order_type == self.ORDER_TYPE_SL:
						# TP was hit, although stop loss order was placed.
						# Cancel SL Order and place market order (at a profit).
						print("Stop Loss order was placed before, but TP was hit !?")
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							# CHECK STATUS OF TP ORDER
							if current_order_info['status'] in [self.exchange.ORDER_STATUS_NEW, \
								self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
								# If not filled, cancel it
								print("If not filled, cancel it.")
								cancel_order_info = self.exchange.cancelOrder(self.symbol, self.current_order_id, is_custom_id=True)
								pprint(cancel_order_info)
								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if current_order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										sold_percentage = Decimal(current_order_info['executedQty'])/self.quantity
										print("Already sold some at a loss:", sold_percentage, "%", "or", Decimal(current_order_info['executedQty']))
										quantity = self.quantity - current_order_info['executedQty']
									print("Remaining quantity:", quantity, "\nPlacing market order to get rid of this.")
									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, amount=quantity, side="SELL", custom_id=order_id)
									pprint(new_order)
									if self.exchange.isValidResponse(new_order):
										self.current_order_id = order_id
										self.current_order_type = self.ORDER_TYPE_SL
										self.is_order_placed = True
										print("Success placing Market order! New Order Id:", self.current_order_id)
									else:
										print(EXCHANGE_INVALID_RESPONSE)

							elif current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								print("SL order was filled :( Too bad...")
								self.is_order_closed = True
								self.is_order_profitable = False 
							else:
								print("Waiting for order to fill, current status: {}".format(current_order_info['status']))

					elif self.current_order_type == self.ORDER_TYPE_TP:
						# Check order with exchange to see if it was filled
						# If it was, close connection, order was complete!
						print("Take Profit order was placed before.")
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								print("Order was filled so OCO is CLOSED!")
								self.is_order_closed = True
								self.is_order_profitable = True 
							else:
								print("Waiting for order to fill, current status: {}".format(order_info['status']))
						else:
							print(EXCHANGE_INVALID_RESPONSE)
				else:
					# An order was not placed before. Place a Market Order to exit trade (for profit).
					print("An order was not placed before. Place a Limit Order (for profit)")
					order_id = uuid4()
					new_order = self.exchange.placeLimitOrder(symbol=self.symbol, 
					price=self.take_profit, amount=self.quantity, side="SELL", custom_id=order_id)
					pprint(new_order)
					if self.exchange.isValidResponse(new_order):
						self.current_order_id = order_id
						self.current_order_type = self.ORDER_TYPE_SL
						self.is_order_placed = True
						print("Success placing Market order! New Order Id:", self.current_order_id)
					else:
						print(EXCHANGE_INVALID_RESPONSE)
			
			else:
				print("Current price is between take profit and stop loss prices.")
				# Current price is between take profit and stop loss prices.
				if self.stop_loss < price and price < self.sl_plus_one_3_diff:
					print("Price closer to stop loss than take profit !")
					#	Price is within 1/3 distance of Stop Loss, we should have a stop loss order placed.
					if self.is_order_placed:
						# There's an order already placed. Is it the right one?
						if self.current_order_type == self.ORDER_TYPE_SL:
							# We have the right order placed, do nothing.
							print("SL Order Already Placed...")
							current_order_info = self.getCurrentOrderInfo()
							if current_order_info is not False:
								if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
									# Order was filled so OCO is CLOSED!
									print("Order was filled so OCO is CLOSED!")
									self.is_order_closed = True
									self.is_order_profitable = False 

						elif self.current_order_type == self.ORDER_TYPE_TP:
							print("TP Order Placed! Need to cancel it and place a SL order.")
							# We don't have the right order placed, cancel current order and place a new one.
							if self.current_order_id == None:
								raise Exception("current_order_id is None despite an order appearing to be placed.")


							cancel_response = self.exchange.cancelOrder(self.symbol, self.current_order_id, is_custom_id=True)
							pprint(cancel_response)
							if self.exchange.isValidResponse(cancel_response):
								# TODO: (Make use of DB persistency, get order_id from DB)
								print("Canceled.")
								self.current_order_id = None
								self.current_order_type = None
								order_id = uuid4()
								response = self.exchange.placeStopLossLimitOrder(
									symbol=self.symbol, amount=self.quantity, side=self.side, 
									stop_price=price, price=self.stop_loss, custom_id=order_id)
								pprint(response)
								if self.exchange.isValidResponse(response):
									self.current_order_id = order_id
									self.current_order_type = self.ORDER_TYPE_SL
									self.is_order_placed = True
									print("Success placing SL Market order! New Order Id:", self.current_order_id)
							else:
								# Unable to cancel order. Try again next time.
								print("Unable to cancel order... Try again next time.")
						else:
							# There's a problem, throw an exception.
							print("It seems like there's an order placed, but it's neither SL nor TP....")
							raise Exception("It seems like there's an order placed, but it's neither SL nor TP.")
					else:
						# There's no order placed. Need to place a SL Order. 
						# TODO: (Make use of DB persistency, get order_id from DB)
						print("There's no order placed. Need to place a SL Order. ")
						order_id = uuid4()
						print(order_id)
						response = self.exchange.placeStopLossLimitOrder(symbol=self.symbol, amount=self.quantity, 
							side=self.side, stop_price=price, price=self.stop_loss, custom_id=order_id)
						pprint(response)
						if self.exchange.isValidResponse(response):
							self.current_order_id = order_id
							self.current_order_type = self.ORDER_TYPE_SL
							print("Success placing SL Market order! New Order Id:", self.current_order_id)
				
				elif self.sl_plus_one_3_diff <= price and price <= self.sl_plus_two_3_diff:
					#	Price is within 1/3 and 2/3 distance of Stop Loss and Take Profit. Do Nothing.
					print("Price is in the middle... Do Nothing.")
				elif self.sl_plus_two_3_diff < price and price < self.take_profit:
					# Price is within 1/3 of take profit, we should have a take profit order placed.
					print("Price closer to take profit than stop loss !")
					if self.is_order_placed:
						# There's an order already placed. Is it the right one?
						if self.current_order_type == self.ORDER_TYPE_SL:
							# We don't have the right order placed, cancel current order and place a new one.
							print("SL Order Placed! Need to cancel it and place a TP order.")
							if self.current_order_id == None:
								raise Exception("current_order_id is None despite an order appearing to be placed.")
							cancel_response = self.exchange.cancelOrder(self.symbol, self.current_order_id, is_custom_id=True)
							pprint(cancel_response)
							if self.exchange.isValidResponse(cancel_response):
								# TODO: (Make use of DB persistency, get order_id from DB)
								print("Canceled, now place TP order")
								self.current_order_id = None
								self.current_order_type = None
								order_id = uuid4()
								response = self.exchange.placeLimitOrder(
									symbol=self.symbol, amount=self.quantity, side=self.side, 
									price=self.take_profit, custom_id=order_id)
								pprint(response)
								if self.exchange.isValidResponse(response):
									self.current_order_id = order_id
									self.current_order_type = self.ORDER_TYPE_TP
									self.is_order_placed = True
									print("Success placing TP! New Order ID:", self.current_order_id)
							else:
								# There was an error cancelling order from exchange. Try again next time!
								print("There was an error cancelling order from exchange. Try again next time!")
						
						elif self.current_order_type == self.ORDER_TYPE_TP:
							# We have the right order placed, do nothing.
							print("TP Order Already Placed...")
							current_order_info = self.getCurrentOrderInfo()
							if current_order_info is not False:
								if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
									# Order was filled so OCO is CLOSED!
									print("Order was filled so OCO is CLOSED!")
									self.is_order_closed = True
									self.is_order_profitable = True 
						else:
							# There's a problem, throw an exception.
							print("It seems like there's an order placed, but it's neither SL nor TP....")
							raise Exception("It seems like there's an order placed, but it's neither SL nor TP.")
					else:
						# There's no order placed. Need to place a TP Order. 
						# TODO: (Make use of DB persistency, get order_id from DB)
						print("There's no order placed. Need to place a TP Order. ")
						order_id = uuid4()
						response = self.exchange.placeLimitOrder(symbol=self.symbol, amount=self.quantity, 
							side=self.side, price=self.take_profit, custom_id=order_id)
						pprint(response)
						if self.exchange.isValidResponse(response):
							self.current_order_id = order_id
							self.current_order_type = self.ORDER_TYPE_TP
							self.is_order_placed = True
							print("Success placing TP! New Order ID:", self.current_order_id)
			
			
			print("Information of current order:")
			current_order_info = self.getCurrentOrderInfo()
			pprint(current_order_info)

			if self.is_order_closed:
				print("OCO Order is closed!")
				if self.is_order_profitable:
					print("YAY! OCO order was profitable")
				else:
					print("NOO! OCO order was not profitable")
				print("Closing down this websocket...")
				self.ws.close()
			print("End message...\n")


	def getCurrentOrderInfo(self):
		order_info = self.exchange.getOrder(self.symbol, self.current_order_id, is_custom_id=True)
		if self.exchange.isValidResponse(order_info):
			return order_info

		return False
		