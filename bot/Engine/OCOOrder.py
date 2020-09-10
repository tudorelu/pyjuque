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
			print('opened connection on', symbol)

	def on_close(self):
		if self.verbose > 0:
			print('closed connection')

	def on_message(self, message):

			if self.verbose > 1:
				print("\nStart message...")

			json_message = json.loads(message)
			# pprint(json_message)
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
					
				if self.is_order_placed:

					# An order was already placed before, what type was it?
					if self.current_order_type == self.ORDER_TYPE_SL:
						if self.verbose > 1:
							print("Stop Loss order was placed before.")
						# Stop Loss order was placed before.
						# Check order with exchange to see if it was filled.
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								if self.verbose > 1:
									print("Order was filled so OCO is CLOSED!")
								self.is_order_closed = True
								self.is_order_profitable = False 
							else:
								if self.verbose > 1:
									print("Waiting for order to fill, current status: {}".format(
										current_order_info['status']))

					elif self.current_order_type == self.ORDER_TYPE_TP:
						# Stop loss was hit, although take profit order was placed.
						# Cancel TP Order and place market order to exit trade (at a loss).
						if self.verbose > 1:
							print("Stop Loss hit but TP was placed before !?")
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							# CHECK STATUS OF TP ORDER
							if current_order_info['status'] in [self.exchange.ORDER_STATUS_NEW, \
								self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
								# If not filled, cancel it
								
								cancel_order_info = self.exchange.cancelOrder(
									self.symbol, 
									self.current_order_id, 
									is_custom_id=True)
								
								if self.verbose > 1:
									print("If not filled, cancel it.")
									pprint(cancel_order_info)
								
								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if current_order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										sold_percentage = Decimal(current_order_info['executedQty'])/self.quantity
										if self.verbose > 1:
											print("Already sold some for a profit of {}%  (price: {})".format(
												sold_percentage, 
												Decimal(current_order_info['executedQty'])))

										quantity = self.quantity - Decimal(current_order_info['executedQty'])

									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, 
										amount=quantity, 
										side="SELL", 
										custom_id=order_id,
										verbose=self.verbose)

									if self.verbose > 1:
										print("Remaining quantity {} \nPlacing market order to get rid of this.".format(quantity))
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

							elif current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								if self.verbose > 0:
									print("TP order filled! Success!")
								self.is_order_closed = True
								self.is_order_profitable = True 		
							else:
								if self.verbose > 1:
									print("Waiting for order to fill, current status: {}".format(current_order_info['status']))	
				else:
					# An order was not placed before. Place a Market Order (at a loss)

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
				
				if self.is_order_placed:
					# Order was placed before, check what type it was
					if self.current_order_type == self.ORDER_TYPE_SL:
						# TP was hit, although stop loss order was placed.
						# Cancel SL Order and place market order (at a profit).
						if self.verbose > 1:
							print("Stop Loss order was placed before, but TP was hit !?")
						current_order_info = self.getCurrentOrderInfo()
						if current_order_info is not False:
							# CHECK STATUS OF TP ORDER
							if current_order_info['status'] in [self.exchange.ORDER_STATUS_NEW, \
								self.exchange.ORDER_STATUS_PARTIALLY_FILLED]:
								# If not filled, cancel it
								cancel_order_info = self.exchange.cancelOrder(self.symbol, self.current_order_id, is_custom_id=True)
								if self.verbose > 1:
									print("If not filled, cancel it.")
									pprint(cancel_order_info)

								if self.exchange.isValidResponse(cancel_order_info):
									order_id = uuid4()
									quantity = self.quantity
									if current_order_info['status'] == self.exchange.ORDER_STATUS_PARTIALLY_FILLED:
										sold_percentage = Decimal(current_order_info['executedQty'])/self.quantity
										if self.verbose > 1:
											print("Already sold some at a loss {}% (price {})".format(
												sold_percentage, 
												Decimal(current_order_info['executedQty'])))
										quantity = self.quantity - current_order_info['executedQty']

									new_order = self.exchange.placeMarketOrder(
										symbol=self.symbol, 
										amount=quantity, 
										side="SELL", 
										custom_id=order_id,
										verbose=self.verbose)
									
									if self.verbose > 1:
										print("Remaining quantity {} \n" +
										"Placing market order to get rid of this.".format(quantity))
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

							elif current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								if self.verbose > 1:
									print("SL order was filled :( Too bad...")
								self.is_order_closed = True
								self.is_order_profitable = False 
							else:
								if self.verbose > 1:
									print("Waiting for order to fill, " +
									"current status: {}".format(current_order_info['status']))

					elif self.current_order_type == self.ORDER_TYPE_TP:
						# Check order with exchange to see if it was filled
						# If it was, close connection, order was complete!
						if self.verbose > 1:
							print("Take Profit order was placed before.")

						current_order_info = self.getCurrentOrderInfo()

						if current_order_info is not False:
							if current_order_info['status'] == self.exchange.ORDER_STATUS_FILLED:
								# Order was filled so OCO is CLOSED!
								if self.verbose > 1:
									print("Order was filled so OCO is CLOSED!")
								self.is_order_closed = True
								self.is_order_profitable = True 
							else:
								if self.verbose > 1:
									print("Waiting for order to fill, current status: {}".format(current_order_info['status']))
						else:
							if self.verbose > 1:
								print(EXCHANGE_INVALID_RESPONSE)
				else:
					# An order was not placed before. Place a Limit Order to exit trade (for profit).

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
			
			if self.verbose > 0:
				if self.is_order_placed:
					print("Information of current order:")
					current_order_info = self.getCurrentOrderInfo()
					pprint(current_order_info)

			if self.verbose > 0:
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
		