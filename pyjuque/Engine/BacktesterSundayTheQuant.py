'''
-> Open Long/Short position
-> Close Position
-> Set Take Profit
-> Set Stop Loss

'''

import pandas as pd 
import numpy as np 


class Backtester():
	def __init__(self, init_params = {}):
		self.init_params = init_params
		self.initial_balance = init_params['initial_balance']
		self.balance = initial_balance
		self.amount = 0
		self.leverage = init_params['leverage']
		self.fee_cost = 0.02 / 100

		self.inv = self.balance * 0.01 * self.leverage

		self.profit = []
		self.drawdown = []
		self.winned = 0
		self.lossed = 0

		self.num_operations = 0
		self.num_longs = 0
		self.num_shorts = 0

		self.is_long_open = False
		self.is_short_open = False

		self.trailing_stop_loss = trailing_stop_loss
		self.from_opened = 0

	def reset_results(self):

		self.balance = self.initial_balance
		self.amount = 0
		self.profit = []
		self.drawdown = []
		self.winned = 0
		self.lossed = 0
		self.num_operations = 0
		self.num_longs = 0
		self.num_shorts = 0
		self.is_long_open = False
		self.is_short_open = False
		self.from_opened = 0
		
	def open_position(self, price, side, from_opened = 0):
		self.num_operations += 1

		if side == 'long':
			self.num_longs += 1

			# comment
			if self.is_short_open:
				self.close_position(price)

			if self.is_long_open:
				self.long_open_price = (self.long_open_price + price)/2
				self.amount += self.inv/price

			else:
				self.is_long_open = True
				self.long_open_price = price
				self.amount = self.inv/price
			

		elif side == 'short':
			self.num_shorts += 1

			# comment
			if self.is_long_open:
				self.close_position(price)


			if self.is_short_open:
				self.short_open_price = (self.short_open_price + price)/2
				self.amount += self.inv/price

			else:
				self.is_short_open = True
				self.short_open_price = price
				self.amount = self.inv/price
			
		# self.amount = self.inv/price

		if self.trailing_stop_loss:
			self.from_opened = from_opened


	def close_position(self, price):
		self.num_operations += 1

		if self.is_long_open:
			result = self.amount * (self.long_open_price - price)
			self.is_long_open = False
			self.long_open_price = 0


		elif self.is_short_open:
			result = self.amount * (price - self.short_open_price)
			self.is_short_open = False
			self.short_open_price = 0


		self.profit.append(result)
		self.balance += result

		if result > 0:
			self.winned += 1
			self.drawdown.append(0)
		else:
			self.lossed += 1
			self.drawdown.append(result)

		self.take_profit_price = 0
		self.stop_loss_price = 0

	def set_take_profit(self, price, tp_long = 1.01, tp_short = 0.99):
		# Here you could pass the tp long/short

		# tp_long = self.init_params['tp_long']
		# tp_short = self.init_params['tp_short']

		if self.is_long_open:
			self.take_profit_price = price * tp_long

		elif self.is_short_open:
			self.take_profit_price = price * tp_short

	def set_stop_loss(self, price, sl_long = 0.99, sl_short = 1.01):

		# Here you could pass the sl long/short

		# sl_long = self.init_params['sl_long']
		# sl_short = self.init_params['sl_short']

		if self.is_long_open:
			self.stop_loss_price = price * sl_long

		if self.is_short_open:
			self.stop_loss_price = price * sl_short

	def return_results(self, symbol, start_date, end_date):
		# And here also you could pasa symbol and period of backtest
		# symbol = self.init_params['symbol']
		# start_date = self.init_params['start_date']
		# end_date = self.init_params['end_date']
		
		profit = sum(self.profit)
		drawdown = sum(self.drawdown)

		fees = (abs(profit) * self.fee_cost * self.num_operations)

		results = {
		'symbol' : symbol,
		'start_date': start_date,
		'end_date': end_date,
		'balance' : self.balance,
		'profit' :	profit,
		'drawdown': drawdown,
		'profit_after_fees': profit - fees,
		'num_operations' : self.num_operations,
		'num_long' : self.num_longs,
		'num_shorts': self.num_shorts,
		'winned' : self.winned,
		'lossed' : self.lossed

		}

		if self.num_operations > 0:
			winrate = self.winned / self.num_operations
			results['winrate'] = winrate
			results['fitness_function'] = ( ( profit - abs(drawdown) ) * winrate)/self.num_operations

		else:
			results['winrate'] = 0
			results['fitness_function'] = 0


		return results


	def backtest(df, strategy):

		high = df['high']
		close = df['close']
		low = df['low']

		for i in range(len(df)):
			if self.balance > 0:

				if strategy.checkLongSignal(i):
					self.open_position(price = close[i], side = 'long', from_opened = i)

					# Son variables que tambien podemos optimizar si definimos
					# como parte del gen y las pasamos a esta funcion.

					self.set_take_profit(price = close[i], tp_long = 1.03)
					self.set_stop_loss(price = close[i], sl_long = 0.99)

				elif strategy.checkShortSignal(i):
					self.open_position(price = close[i], side = 'short', from_opened = i)

					# Son variables que tambien podemos optimizar si definimos
					# como parte del gen y las pasamos a esta funcion.

					self.set_take_profit(price = close[i], tp_short = 0.97)
					self.set_stop_loss(price = close[i], sl_short = 1.01)

				else:
					
					if self.trailing_stop_loss and (self.is_long_open or self.is_short_open):

						new_max = high[self.from_opened : i].max()
						previous_stop_loss = self.stop_loss_price
						self.set_stop_loss(price = new_max)
						if previous_stop_loss > self.stop_loss_price:
							self.stop_loss_price = previous_stop_loss

					if self.is_long_open:

						if high[i] >= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
						elif low[i] <= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)

					elif self.is_short_open:

						if high[i] >= self.stop_loss_price:
							self.close_position(price = self.stop_loss_price)
						elif low[i] <= self.take_profit_price:
							self.close_position(price = self.take_profit_price)
		
