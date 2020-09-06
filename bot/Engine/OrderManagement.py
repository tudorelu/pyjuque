
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

		# get pair from database
		pair:Pair = self.bot.getPairWithSymbol(self.session, order.symbol)
		# get info of order from exchange
		exchange_order_info = exchange.getOrderInfo(order.symbol, order.id)

		# check for valid response from exchange
		if not exchange.isValidResponse(exchange_order_info):
			logging.warning('Exchange order info could not be retrieved!')
			return
		
		# update order params.
		order.side = exchange_order_info['side']
		order.status = exchange_order_info['status']
		order.executed_quantity = exchange_order_info['executedQty']

		# Order has been canceled by the user
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_CANCELED):
			self.process_canceled_buy_order(order, pair)

		# buy order was filled, place exit order.
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_FILLED):
			self.try_exit_order(order, pair)

		# buy order has been accepted by engine
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_NEW):
			self.update_open_buy_order(order, pair)

		# buy order that has been partially filled
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
			self.update_partially_filled_buy_order(order, pair)

		# buy order was rejected, not processed by engine
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_REJECTED):
			self.process_rejected_buy_order(order, pair)

		# buy order expired, i.e. FOK orders with no fill or due to maintenance by exchange.
		if (order.side == 'BUY') & (order.status == exchange.ORDER_STATUS_EXPIRED):
			self.process_expired_buy_order(order, pair)

		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_CANCELED):
			self.process_canceled_sell_order(order, pair)

		# sell order was filled
		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_FILLED):
			self.process_filled_sell_order(order)

		# sell order was accepted by engine of exchange
		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_NEW):
			self.update_open_sell_order(order)

		# sell order was partially filled
		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_PARTIALLY_FILLED):
			self.update_partially_filled_sell_order(order)

		# sell order was rejected by engine of exchange
		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_REJECTED):
			self.process_rejected_sell_order(order)

		# sell order expired, i.e. due to FOK orders or partially filled market orders
		if (order.side == 'SELL') & (order.status == exchange.ORDER_STATUS_EXPIRED):
			self.process_expired_sell_order(order)

		self.session.commit() 

	def process_canceled_buy_order(self, order, pair):
		""" 
		Processes a canceled buy order. 
		"""
		if order.executed_quantity > 0:
			self.try_exit_order(order, pair) 
		else:
			order.is_closed = True
			pair.active = True
			pair.current_order_id = None
		
	def update_open_buy_order(self, order, pair):
		"""
		updates an open buy order based on given strategy
		"""
		exchange = self.exchange
		strategy = self.strategy
		# TODO probably also want to get limit and time interval from settings file.
		candlestick_data = exchange.getSymbolKlines(order.symbol, "5m", limit=100)
		# TODO might want to make this refresh() s.t. only computes indicators for only new candles
		strategy.setup(candlestick_data)
		# TODO create update_open_buy_order method in strategy
		cancel_order = strategy.update_open_buy_order()
		if cancel_order:
			order_result = exchange.cancelOrder(order.symbol, order.id)
			if exchange.isValidResponse(order_result):
				order.executed_quantity = order_result['executedQty']
				order.status = order_result['status']
				self.process_canceled_buy_order(order, pair)

	def update_partially_filled_buy_order(self, order, pair):
		"""
		updates a partially filled buy order based on given strategy
		"""
		exchange = self.exchange
		strategy = self.strategy

		# TODO probably also want to get limit and time interval from settings file.
		candlestick_data = exchange.getSymbolKlines(order.symbol, '5m', limit=100)
		# TODO might want to make this refresh() s.t. only computes indicators for only new candles
		strategy.setup(candlestick_data)
		# TODO create update_partially_filled_buy_order method in strategy
		cancel_order = strategy.update_partially_filled_buy_order(order)
		if cancel_order:
			order_result = exchange.cancelOrder(order.symbol, order.id)
			if exchange.isValidResponse(order_result):
				order.executed_quantity = order_result['executedQty']
				order.status = order_result['status']
				self.process_canceled_buy_order(order, pair)

	def process_rejected_buy_order(self, order, pair):
		""" 
		The order was not accepted by the engine and not processed. 
		Therefore, delete the order from the database. 
		"""
		order.is_closed = True
		pair.active = True
		pair.current_order_id = None
	
	def process_expired_buy_order(self, order, pair):
		"""
		The order was canceled according to the order type's rules 
		(e.g. LIMIT FOK orders with no fill, LIMIT IOC or MARKET orders that partially fill)
		or by the exchange, (e.g. orders canceled during liquidation, orders canceled during maintenance)
		"""
		if order.executed_quantity > 0:
			self.process_canceled_buy_order(order, pair)
		else:
			order.is_closed = True
			pair.active = True
			pair.current_order_id = None
		
	def process_canceled_sell_order(self, order, pair):
		"""
		Process a canceled sell order.
		Redundant I think, status is only CANCELED IF CANCELED BY USER.
		Probably still want user to be able to interfere manually.
		"""
		self.try_exit_order(order, pair)
		# order.is_closed = True
		# pair.active = True
		# pair.current_order_id = None
	
	def update_open_sell_order(self, order, pair):
		"""
		Update open sell order based on given strategy.
		"""

		exchange = self.exchange
		strategy = self.strategy
		candlestick_data = exchange.getSymbolKlines(order.symbol, '5m', 100)
		strategy.setup(candlestick_data)
		
		update_sell_order, exit_params, order_type = strategy.update_open_sell_order()

		if update_sell_order:
			order_result = exchange.cancelOrder(order.symbol, order.id)
			if exchange.isValidResponse(order_result):
				order.status = order_result['status']
				order.executed_quantity = order_result['executedQty']
				self.placeOrder(exit_params, order, order_type, pair)
	
	def update_partially_filled_sell_order(self, order):
		"""
		Update partially filled sell order based on given strategy.
		"""
		pass

	def process_rejected_sell_order(self, order):
		"""
		Process rejected sell order that was rejected by exchange
		"""
		pass

	def process_expired_sell_order(self, order):
		"""
		Process expired sell order.
		"""
		pass

	def process_filled_sell_order(self, order):
		"""
		Process filled sell order.
		"""
		pass
	
	def try_exit_order(self, order, pair):

		symbol = order.symbol
		bot = self.bot
		session = self.session
		exchange = self.exchange
		strategy = self.strategy

		candlestick_data  = exchange.getSymbolKlines(symbol, '5m', 100)
		strategy.setup(candlestick_data)

		# TODO strategy class needs to take status etc in to account when computing exit params
		order_type, exit_params = strategy.compute_exit_params(order)
		exit_params['quantity'] = self.compute_quantity(order)

		self.placeOrder(exit_params, order, order_type, pair)
		
	def placeOrder(self, exit_params, order, order_type, pair):
		"""
		 Place non-entry order
		"""
		exchange = self.exchange
		bot = self.bot
		session = self.session

		if not order.is_test:		
			print("Entry order, place exit order! on", order.symbol)
			# Create ids for order by uuid4 for example.
			new_order_model = self.create_Order(order_type, order, exit_params)
			new_order_response = dict()
			new_order_response = order_type(new_order_model)

			if exchange.isValidResponse(new_order_response):
				exchange.updateSQLOrderModel(new_order_model, new_order_response, bot)
				new_order_model.matched_order_id = order.id
				order.is_closed = True
				order.matched_order_id = new_order_model.id
				pair.active = False
				pair.current_order_id = new_order_model.id
				session.add(new_order_model)		

	def compute_quantity(self, order):
		if order.side == 'BUY':
			exit_quantity = order.executed_quantity
		elif order.side == 'SELL':
			exit_quantity = order.desired_quantity - order.executed_quantity
		return exit_quantity
	
	def create_Order(self, order_type, order, exit_params):
		# Create ids from uuid instead of letting databse do it.
		bot = self.bot
		if order_type == self.exchange.placeLimitOrder:
			new_order_model =  Order(
									bot_id = bot.id,
									symbol = order.symbol,
									status = "NEW",
									side = exit_params['side'], 
									is_entry = False, 
									entry_price = exit_params['entry_price'], 
									stop_loss_price = exit_params['stop_loss_price'], 
									original_quantity = exit_params['quantity'],
									executed_quantity = 0,
									is_closed = False, 
									is_test = bot.test_run)
		return new_order_model


