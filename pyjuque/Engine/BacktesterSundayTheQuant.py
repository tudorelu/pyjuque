'''
-> Open Long/Short position
-> Close Position
-> Set Take Profit
-> Set Stop Loss

'''

import pandas as pd 
import numpy as np 


class Backtester():

    def __init__(self, params = {}):
        self.params = params
        self.initial_balance = 0

        for elem in ['starting_balance', 'entry_settings', 'exit_settings', 'strategy']:
            assert elem in list(params.keys()), 'Key {} should be inside the params dict! '.format(elem)
        
        self.initial_balance = params['starting_balance']
        
        self.leverage = 1
        if params['entry_settings'].__contains__('leverage'):
            self.leverage = params['entry_settings']['leverage']
        self.initial_entry_allocation = 100
        if params['entry_settings'].__contains__('initial_entry_allocation'):
            self.initial_entry_allocation = params['entry_settings']['initial_entry_allocation']

        self.take_profit = 1.05
        if params['exit_settings'].__contains__('take_profit'):
            self.take_profit = (100 + params['exit_settings']['take_profit']) / 100
        self.stop_loss_value = 0
        if params['exit_settings'].__contains__('stop_loss_value'):
            self.stop_loss_value = (100 - params['exit_settings']['stop_loss_value']) / 100
        self.trailing_stop_loss = False
        if params['exit_settings'].__contains__('trailing_stop_loss'):
            self.trailing_stop_loss = params['exit_settings']['trailing_stop_loss']
        self.exit_on_short = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_short = params['exit_settings']['exit_on_signal']
        self.exit_on_long = False
        if params['exit_settings'].__contains__('exit_on_signal'):
            self.exit_on_long = params['exit_settings']['exit_on_signal']

        self.strategy = params['strategy']['class'](**params['strategy']['params'])

        self.amount = 0
        self.fee_cost = 0.1 / 100
        self.balance = self.initial_balance
        self.locked_in_trades = 0
        self.locked_trades = 0
        self.first_price = 0
        self.last_price = 0
        self.unrealised_profits = 0
        self.open_positions = 0

        self.inv = self.balance * (self.initial_entry_allocation / 100) * self.leverage

        self.profit = []
        self.drawdown = []

        self.entries = []
        self.exits = []
        self.winned = 0
        self.lossed = 0

        self.num_operations = 0
        self.num_longs = 0
        self.num_shorts = 0

        self.is_long_open = False
        self.is_short_open = False
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
        self.locked_in_trades = 0
        self.locked_trades = 0
        self.last_price = 0
        self.unrealised_profits = 0
        self.open_positions = 0


    def open_position(self, price, time, side, from_opened = 0):
        self.num_operations += 1
        if side == 'long':
            self.num_longs += 1
            # comment
            # if self.is_short_open and self.exit_on_long:
            #     self.close_position(price)
            if self.is_long_open:
                self.long_open_price = (self.long_open_price + price)/2
                self.amount += self.inv #* price
            else:
                self.is_long_open = True
                self.long_open_price = price
                self.amount = self.inv #* price
            self.entries.append([time, price, self.inv, self.inv / price]) #* price ])
        # elif side == 'short':
        #     self.num_shorts += 1
        #     # comment
        #     if self.is_long_open and self.exit_on_short:
        #         self.close_position(price)
        #     elif self.is_short_open:
        #         self.short_open_price = (self.short_open_price + price)/2
        #         self.amount += self.inv #* price
        #     else:
        #         self.is_short_open = True
        #         self.short_open_price = price
        #         self.amount = self.inv #* price
        #     self.entries.append([time, price, self.inv, self.inv / price ]) #* price ])
        self.balance -= self.inv
        self.open_positions += 1
        # self.amount = self.inv/price
        if self.trailing_stop_loss:
            self.from_opened = from_opened


    def close_position(self, price, time):
        self.num_operations += 1
        if self.is_long_open:
            result = self.amount * (price - self.long_open_price)
            self.is_long_open = False
            self.long_open_price = 0
        # elif self.is_short_open:
        #     result = self.amount * (self.short_open_price - price)
        #     self.is_short_open = False
        #     self.short_open_price = 0
        self.profit.append(result)
        self.exits.append([time, price, self.amount, self.amount / price])
        # print('closing position! {}, {} amount was {}'.format(time, price, self.amount))
        self.balance += self.inv * self.open_positions
        self.open_positions = 0
        self.amount = 0
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
        # tp_long = self.params['tp_long']
        # tp_short = self.params['tp_short']
        if self.is_long_open:
            self.take_profit_price = price * tp_long
        # elif self.is_short_open:
        #     self.take_profit_price = price * tp_short


    def set_stop_loss(self, price, sl_long = 0.99, sl_short = 1.01):
        # Here you could pass the sl long/short
        # sl_long = self.params['sl_long']
        # sl_short = self.params['sl_short']
        if self.is_long_open:
            self.stop_loss_price = price * sl_long
        # if self.is_short_open:
        #     self.stop_loss_price = price * sl_short


    def return_results(self):
        # And here also you could pass symbol and period of backtest
        # symbol = self.params['symbol']
        # start_date = self.params['start_date']
        # end_date = self.params['end_date']
        buy_n_hold = self.initial_balance * (self.last_price / self.first_price)
        profit = sum(self.profit) / self.last_price
        drawdown = sum(self.drawdown)
        fees = (abs(profit) * self.fee_cost * self.num_operations) / self.last_price
        winrate = 0
        if (self.winned + self.lossed) > 0:
            winrate = self.winned / (self.winned + self.lossed)

        results = {
            'balance_initial' : self.initial_balance,
            'balance_locked' : self.initial_balance - self.balance,
            'balance_free' : self.balance,
            'balance_plus_profits': self.balance + profit,
            'profit' :	profit + self.unrealised_profits,
            'profit_realised': profit, 
            'profit_unrealised' : self.unrealised_profits,
            'profit_buy_and_hold' : buy_n_hold - self.initial_balance,
            # 'drawdown': drawdown,
            # 'entries': self.entries,
            # 'exits': self.exits,
            'profit_after_fees': profit - fees,
            'n_trades' : self.num_operations,
            'n_long' : self.num_longs,
            'n_shorts': self.num_shorts,
            'n_locked_trades': self.locked_trades,
            'winned' : self.winned,
            'lossed' : self.lossed,
            'winrate' : winrate
        }
        # results['fitness_function'] = ( ( profit - abs(drawdown) ) * winrate) / self.num_operations
        return results


    def backtest(self, df):
        high = df['high']
        close = df['close']
        low = df['low']
        time = df['time']

        self.strategy.setUp(df)

        for i in range(len(df)):

            # Check Signals
            long_signal = self.strategy.checkLongSignal(i)
            short_signal = self.strategy.checkShortSignal(i)
            
            # Close Existing Trades if Open
            if self.is_long_open:
                if self.exit_on_short and short_signal:
                    self.close_position(price = close[i], time = time[i])
                elif high[i] >= self.take_profit_price:
                    self.close_position(price = self.take_profit_price, time = time[i])
                elif low[i] <= self.stop_loss_price:
                    self.close_position(price = self.stop_loss_price, time = time[i])
            # elif self.is_short_open:
            #     if self.exit_on_long and long_signal:
            #         self.close_position(price = close[i], time = time[i])
            #     elif high[i] >= self.stop_loss_price:
            #         self.close_position(price = self.stop_loss_price, time = time[i])
            #     elif low[i] <= self.take_profit_price:
            #         self.close_position(price = self.take_profit_price, time = time[i])
                
            if self.balance > 0:
                # Open New Trades If We Received Signals
                if long_signal:
                    self.open_position(price = close[i], time = time[i], side = 'long', from_opened = i)
                    self.set_take_profit(price = close[i], tp_long = self.take_profit)
                    self.set_stop_loss(price = close[i], sl_long = self.stop_loss_value)
                # elif short_signal:
                #     self.open_position(price = close[i], time = time[i], side = 'short', from_opened = i)
                #     self.set_take_profit(price = close[i], tp_short = self.take_profit)
                #     self.set_stop_loss(price = close[i], sl_short = self.stop_loss_value)
                        
            # Update Trailing Stop Loss If Available
            if self.trailing_stop_loss and (self.is_long_open): # or self.is_short_open):
                new_max = high[self.from_opened : i].max()
                previous_stop_loss = self.stop_loss_price
                self.set_stop_loss(price = new_max)
                if previous_stop_loss > self.stop_loss_price:
                    self.stop_loss_price = previous_stop_loss
                

        self.first_price = close[0]
        last_price = close[len(close) - 1]
        last_exit = self.exits[len(self.exits) - 1]
        remaining_amount = 0
        unrealised_profits = 0
        locked_trades = 0
        for entry in self.entries:
            if entry[0] > last_exit[0]:
                remaining_amount += entry[2]
                unrealised_profits += entry[2] / entry[1]
                locked_trades += 1
        # self.locked_in_trades = remaining_amount 
        self.last_price = last_price
        self.locked_trades = locked_trades
        self.unrealised_profits = (remaining_amount / last_price - unrealised_profits) #/ last_price
        

