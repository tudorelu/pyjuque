
from bot.Exchanges.Binance import Binance
from pandas import DataFrame
import logging
from traceback import print_exc

from decimal import Decimal
from datetime import datetime
from bot.Engine.Models import Bot, Pair, Order

class OrderManagement:

	def __init__(self, session, bot, exchange, strategy):
		self.bot = bot
		self.session = session
		self.exchange = exchange
		self.strategy = strategy	

	def execute_bot(self):
			""" The main execution loop of the bot """

			# Step 1: Retreive all paris for a particular bot
			print("Getting active pairs:")
			active_pairs = self.bot.getActivePairs(self.session)
			print(active_pairs)

			# Step 2 For Each Pair:
			#		Retreive current market data 
			# 	Compute Indicators & Check if Strategy is Fulfilled
			#		IF Fulfilled, palce order (Save order in DB)
			print("Checking signals on pairs...")
			for pair in active_pairs:
					self.try_entry_order(pair)

			# Step 3: Retreive all open orders on the bot
			print("Getting open orders:")
			open_orders = self.bot.getOpenOrders(self.session)
			print(open_orders)

			# Step 4: For Each order that was already placed by the bot 
			# and was not filled before, check status:
			#		IF Filled -> If entry order, place exit order
			#							-> If exit order, success (take profit), or 
			# 															failure (stop loss): Resume trading!
			print("Checking orders state...")
			for order in open_orders:
					self.update_open_order(order)

	def try_entry_order(self, pair):
			""" Gets the latest market data and runs the strategy on it.
			If strategy says to buy, it buys. """

			bot = self.bot
			session = self.session
			exchange = self.exchange
			strategy = self.strategy

			symbol = pair.symbol
			print("Checking signal on", symbol)
			df = exchange.getSymbolKlines(symbol, "5m", limit=100)
			l = len(df) - 1
			strategy.setup(df)
			buy_signal = strategy.checkBuySignal(l)
			
			if buy_signal:
					
					print("BUY! on", symbol)
					take_profit = bot.profit_target
					desired_price = Decimal(df['close'][l])
					quote_qty =  Decimal(bot.starting_balance) * Decimal(bot.trade_allocation) / Decimal(100)
					desired_quantity = quote_qty / desired_price
					order = Order(
							bot_id = bot.id, 
							symbol = symbol,
							status = "NEW", 
							side = "BUY", 
							is_entry = True, 
							entry_price=desired_price, 
							original_quantity = desired_quantity,
							executed_quantity = 0,
							is_closed = False, 
							is_test = bot.test_run)

					session.add(order)
					session.commit()
					
					order_response = dict()
					if bot.test_run:
							order_response = dict(message='success')
					else:
							order_response = exchange.placeLimitOrder(
									symbol=symbol, 
									price=desired_price, 
									side="BUY",
									amount=desired_quantity,
									custom_id=order.id)

					if exchange.isValidResponse(order_response):
							print("SUCCESSFUL ORDER! on", symbol)
							bot.current_balance = bot.current_balance - quote_qty
							exchange.updateSQLOrderModel(order, order_response, bot)
							pair.current_order_id = order.id
							pair.active = False
							session.commit()
					else:
							print("ERROR placing order! on", symbol)
							session.query(Order).filter(Order.id==order.id).delete()
							session.commit()

	def update_open_order(self, order):
		""" Checks the status of an open order and tries to update the order """

		exchange = self.exchange

		# get info of order from exchange
		exchange_order_info = exchange.getOrderInfo(order.symbol, order.id)

		# check for valid response from exchange
		if not exchange.isValidResponse(exchange_order_info):
			logging.warning('Exchange order info could not be retrieved!')
			return
		
		order_side = exchange_order_info['side']
		order_status = exchange_order_info['status']
		
		# Order has been canceled by the user
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_CANCELED):
			executed_quantity = exchange_order_info['executedQty']
			self.handle_canceled_buy_order(order, executed_quantity)

		# buy order was filled, place exit order.
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_FILLED):
			self.try_exit_order(order)

		# buy order has been accepted by engine
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_NEW):
			self.update_open_buy_order(order)

		# buy order that has been partially filled
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
			executed_quantity = exchange_order_info['executedQty']
			self.update_partially_filled_buy_order(order, executed_quantity)

		# buy order was rejected, not processed by engine
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_REJECTED):
			self.handle_rejected_buy_order(order)

		# buy order expired, i.e. FOK orders with no fill or due to maintenance by exchange.
		if (order_side == 'BUY') & (order_status == exchange.ORDER_STATUS_EXPIRED):
			self.handle_expired_buy_order(order)

		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_CANCELED):
			executed_quantity = exchange_order_info['executedQty']
			self.handle_canceled_buy_order(order, executed_quantity)

		# sell order was filled
		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_FILLED):
			self.handle_filled_sell_order(order)

		# sell order was accepted by engine of exchange
		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_NEW):
			self.update_open_sell_order(order)

		# sell order was partially filled
		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
			executed_quantity = exchange_order_info['executedQty']
			self.update_partially_filled_sell_order(order, executed_quantity)

		# sell order was rejected by engine of exchange
		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_REJECTED):
			self.handle_rejected_sell_order(order)

		# sell order expired, i.e. due to FOK orders or partially filled market orders
		if (order_side == 'SELL') & (order_status == exchange.ORDER_STATUS_EXPIRED):
			self.handle_expired_sell_order(order)

	def handle_canceled_buy_order(self, order, executed_quantity):
		""" Processes a canceled buy order. """
		pair:Pair = self.bot.getPairWithSymbol(self.session, order.symbol)
		if executed_quantity > 0:
			# TODO process as filled buy order for executed amount.
			pass
		order.executed_quantity = executed_quantity
		order.is_closed = True
		pair.active = True
		pair.current_order_id = None
		self.session.commit()
		
	def update_open_buy_order(self, order):
		exchange = self.exchange
		strategy = self.strategy
		df = exchange.getSymbolKlines(order.symbol, "5m", limit=100)
		# TODO might want to make this refresh() s.t. only computes indicators for only new candles
		strategy.setup(df)
		# TODO create update_open_buy_order method in strategy
		cancel_order = strategy.update_open_buy_order()
		if cancel_order:
			order_result = exchange.cancelOrder(order.symbol, order.id)
			if exchange.isValidResponse(order_result):
				self.handle_canceled_buy_order(order, order_result['executedQty'])

	def update_partially_filled_buy_order(self, order, executed_quantity):
		pass

	def handle_rejected_buy_order(self, order):
		pass
	
	def handle_expired_buy_order(self, order):
		pass

	def try_exit_order(self, order):
			""" Checks whether the order has been filled or not. 
			If it has, and it was an entry order, it places the 
			corresponding exit order. If it was an exit order, it 
			resumes trading on that pair. """

			symbol = order.symbol
			
			bot = self.bot
			session = self.session
			exchange = self.exchange
			strategy = self.strategy
			pair:Pair = bot.getPairWithSymbol(session, symbol)
			order:Order = session.query(Order).get(order.id)

			print("Checking", order, "on", symbol)
			# If order was test (sim), then we need to simulate the market 
			# in order to decide whether it would have been filled or not.
			# TODO: this is accurate for low amounts, if we placed a large 
			# order we need to take volume into account as well
			if order.is_test:
				df = exchange.getSymbolKlines(order.symbol, '5m', 50)
				l = len(df) - 1
				filled = False
				
				# loop through the candles and look at the ones after the order was placed
				for index, row in df.iterrows():
					if datetime.fromtimestamp(row['time']/1000) > order.timestamp:
						if order.is_entry:
							if row['low'] < order.entry_price:
								order.status = exchange.ORDER_STATUS_FILLED
								order.executed_quantity = order.original_quantity
								order.is_closed = True
								filled = True
								session.commit()
								break	

						elif not order.is_entry:
							if row['high'] > Decimal(order.entry_price):
								order.status = exchange.ORDER_STATUS_FILLED
								order.executed_quantity = order.original_quantity
								order.is_closed = True
								filled = True
								session.commit()	
								break
			else:
				exchange_order_info = exchange.getOrderInfo(symbol, order.id)
				if not exchange.isValidResponse(exchange_order_info):
					return
				order.status = exchange_order_info['status']
				order.executed_quantity = exchange_order_info['executedQty']
			
			session.commit()

			# Now check if order was filled
			if order.status == exchange.ORDER_STATUS_FILLED:
					
				print("FILLED!")
				if order.is_entry:
				# If this entry order has been filled, place corresponding exit order
					print("Entry order, place exit order! on", symbol)
					new_order_model = Order(
						bot_id = bot.id,
						symbol = symbol,
						status = "NEW",
						side = "SELL", 
						is_entry = False, 
						entry_price = Decimal(order.entry_price) * (Decimal(100) + bot.profit_target)/Decimal(100), 
						stop_loss_price = Decimal(order.entry_price) * bot.stop_loss_target/Decimal(100), 
						original_quantity = order.executed_quantity,
						executed_quantity = 0,
						is_closed = False, 
						is_test = bot.test_run)

					session.add(new_order_model)
					session.commit()

					exit_price = order.take_profit_price
					
					new_order_response = dict()
					if bot.test_run:
						new_order_response = dict(message="success")
					else:
						new_order_response = exchange.placeLimitOrder(
							symbol = symbol, 
							price = exit_price,
							side = "SELL",
							amount = order.executed_quantity,
							custom_id=new_order_model.id)
						
					if exchange.isValidResponse(new_order_response):
						exchange.updateSQLOrderModel(new_order_model, new_order_response, bot)
						new_order_model.matched_order_id = order.id
						order.is_closed = True
						order.matched_order_id = new_order_model.id
						pair.active = False
						pair.current_order_id = new_order_model.id
						session.commit()
					else:
						session.query(Order).filter(Order.id==new_order_model.id).delete()
						session.commit()
				
				else:
				# If this exit order has been filled, resume trading
					print("Exit order, resume trading! on", symbol)
					order.is_closed = True
					pair.active = True
					pair.current_order_id = None
					session.commit()

			# If the order has been cancelled, set the order to close and start from beginning
			# TODO If exit order was cancelled we shouldn't start from the beginning, we should
			# replace the exit order to get rid of the coins that we bought
			elif order.status == exchange.ORDER_STATUS_CANCELED:
				print("CANCELED! Resume trading on", symbol)
				order.is_closed = True
				pair.active = True
				pair.current_order_id = None
				session.commit()

	def handle_canceled_sell_order(self, order):
		pass

	def update_open_sell_order(self, order):
		pass

	def update_partially_filled_sell_order(self, order, executed_quantity):
		pass

	def handle_rejected_sell_order(self, order):
		pass
	
	def handle_expired_sell_order(self, order):
		pass
	
	def handle_filled_sell_order(self, order):
		pass