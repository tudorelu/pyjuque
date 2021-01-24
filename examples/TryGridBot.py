import sys
from os.path import abspath, join, pardir
sys.path.append(abspath(join(abspath(__file__), pardir, pardir)))

from os import getenv
from yaspin import yaspin
from pprint import pprint
from decimal import Decimal
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from pyjuque.Engine.GridBotController import GridBotController

from traceback import print_exc

import time
import asciichartpy
import curses

'''
from examples.GridBot import GridBot
>>> bot = GridBot('GridBot_OKEX_LTCUSDT_300_15_0point5_live')
>>> bot
<examples.GridBot.GridBot object at 0x10c0d0880>
>>> order = bot.session.query(Order).filter_by(id='36e50b168a72452089ea9e54ff9f3a56').first()
>>> order.position_id
'dbcdf6d28fca41dc932ea274a7965afc'
>>> order.is_entry = True
>>> bot.session.commit()
'''

def populateScreen(bot, open_orders, buy_orders, sell_orders):

    df = bot.exchange.getOHLCV(bot.symbol, '5m', 100)

    buys_plots = []
    sells_plots = []
    plot_colors = [asciichartpy.white]

    min_price = float(min(df['close'].tolist()))
    max_price = float(max(df['close'].tolist()))

    for order in buy_orders:
        p = [float('nan') for i in range(90)]
        p.extend([float(order.price) for i in range(10)])

        if min_price > float(order.price):
            min_price = float(order.price)

        buys_plots.append(p) 
        plot_colors.append(asciichartpy.green)
    
    for order in sell_orders:
        p = [float('nan') for i in range(90)]
        p.extend([float(order.price) for i in range(10)])

        if max_price < float(order.price):
            max_price = float(order.price)

        sells_plots.append(p) 
        plot_colors.append(asciichartpy.red)

    plots = [df['close'].tolist()]
    if len(buys_plots) > 0:
        plots.extend(buys_plots)
    if len(sells_plots) > 0:
        plots.extend(sells_plots)

    max_price = max_price * 1.005
    min_price = min_price * 0.995

    # print(len(plots), len(plot_colors), len(buys_plots), len(sells_plots))
    bot.screen.clear()
    bot.screen.refresh()
    # curses.endwin()

    bot.screen.addstr(1, 1, bot.symbol+' price chart (last price: {})'.format(
        df['close'][len(df)-1]))

    plot_config = { 'height':40, 'min': min_price, 'max':max_price }
    price_plot = asciichartpy.plot(
        df['close'].tolist(), plot_config)
    buy_plot = asciichartpy.plot(
        [df['close'].tolist(), *buys_plots], plot_config)
    sell_plot = asciichartpy.plot(
        [df['close'].tolist(), *sells_plots], plot_config)
    
    k = 3
    for line in price_plot.split('\n'):
        bot.screen.addstr(k, 0, line, curses.color_pair(1))
        k += 1

    k = 3
    for line in buy_plot.split('\n'):
        q = 0
        for char in line:
            if char != chr(bot.screen.inch(k, q)):
                bot.screen.addch(k, q, char, curses.color_pair(2))
            q += 1
        k += 1

    k = 3
    for line in sell_plot.split('\n'):
        q = 0
        for char in line:
            if char != chr(bot.screen.inch(k, q)):
                bot.screen.addch(k, q, char, curses.color_pair(3))
            q += 1
        k += 1
    
    bot.screen.refresh()
    # bot.status_printer.start()


if __name__ == '__main__':
    okex = CcxtExchange('okex', {
        'apiKey': getenv('OKEX_API_KEY'), 
        'secret': getenv('OKEX_API_SECRET'),
        'password': getenv('OKEX_PASSWORD'),
        'timeout': 30000,
        # 'verbose': True,
        'enableRateLimit': True,
    })

    symbol = 'LTC/USDT'
    total_amount = 200          # We are trading in total 1000 units of quote asset 
    trade_amount = 0.05         # For each trade we are placing 10% of total amount
    trade_step = 0.003          # 0.3% space between trades and 2 * 0.3% profit per trade
    total_trades = 1            

    time_to_sleep = 10
    status_printer = yaspin()
    screen = curses.initscr()
    bot = GridBotController() #('GridBot_OKEX_LTCUSDT_300_15_0point5_live')
    bot.status_printer = status_printer
    bot.screen = screen
    bot.create(okex, symbol, total_amount, trade_amount, trade_step, total_trades)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    while True:
        bot.status_printer.stop()

        open_orders = bot.bot.getOpenOrders(bot.session)
        buy_orders = [order for order in open_orders if order.side == 'buy']
        sell_orders = [order for order in open_orders if order.side == 'sell']

        populateScreen(bot, open_orders, buy_orders, sell_orders)
        
        try:
            bot.executeBot()
        except KeyboardInterrupt:
            bot.screen.clear()
            bot.screen.refresh()
            curses.endwin()
            break
        except Exception:
            bot.screen.clear()
            bot.screen.refresh()
            curses.endwin()
            print_exc()
            break

        left_to_sleep = time_to_sleep
        
        while left_to_sleep > 0:
            bot.status_printer.text = '{} bot has {} open orders | {} buy {} sell | {} more seconds...'.format(
                bot.symbol, len(open_orders), len(buy_orders), len(sell_orders), left_to_sleep)
            time.sleep(1)
            left_to_sleep -= 1

