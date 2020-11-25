"""
    Backtester infrastructure supporting
        - stop loss, trailing stop loss &
        - subsequent entries (DCA) logic

    TODO: Needs proper testing.
"""

import pandas as pd
from decimal import Decimal

# HELPER CLASS
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

model_entry_strategy:dotdict = dotdict(dict(
    strategy_class = "some_function",
    args = "some_args",
))

model_entry_settings:dotdict = dotdict(dict(
    # subsequent entries
    se = dotdict(dict(
        times = 1,
        after_profit = 0.995,
        pt_decrease = 0.998,
    ))
))

model_exit_settings:dotdict = dotdict(dict(
    profit_target = 1.045,
    # trailing stop loss
    tsl = dotdict(dict(
        value = 0.97,
        after_profit = 1.01
    )),
    # stop loss
    sl = 0.85
))

def backtest(df, symbol, exchange,
    entry_strategy=model_entry_strategy,
    entry_settings=model_entry_settings,
    exit_settings=model_exit_settings):
    '''
        Function used to backtest a strategy on a dataframe `df`
        containing candlestick data of a coin over a period of time.
        Parameters
        --
            DataFrame df - the container of the candlestick data
            dict sd - the dict containing symbol data
            Exchange exchange - exchange to test this strategy on
            dict `entry_strategy` - details about the entry strategy (function & args)
            dict `entry_settings` - details about the entry settings (subsequent entries)
            dict `exit_settings` - details about the exit settings (stop loss, tsl & take profit)
        Returns
        --
            dict information about the backtesting results
    '''

    assert exit_settings.sl is None or \
        (exit_settings.sl <= Decimal(1) and exit_settings.sl > Decimal(0)), \
        ("stop_loss should be between 0 and 1, not "+str(exit_settings.sl))

    assert exit_settings.tsl is None or \
        (exit_settings.tsl.__contains__('value') and \
            exit_settings.tsl.__contains__('after_profit')), \
        ("tsl (exit) settings should contain `value` and `after_profit` ")

    assert exit_settings.tsl is None or \
        exit_settings.tsl.value > Decimal(0) and \
        exit_settings.tsl.value < Decimal(1), \
        "tsl (exit) settings `value` should be between 0 and 1, not "+str(exit_settings.tsl.value)

    assert exit_settings.tsl is None or \
        exit_settings.tsl.after_profit > Decimal(1), \
        ("tsl (exit) settings `after_profit` should be greater than 1, not "\
        +str(exit_settings.tsl.after_profit))

    assert exit_settings.pt is None or \
        exit_settings.pt  > Decimal(1), \
        ("profit_target should be greater than 1, not "+str(exit_settings.pt))

    # lists containing buy and sell times, for plotting
    buy_times = []
    tp_sell_times = []
    sl_sell_times = []
    tsl_sell_times = []
    tsl_active_times = []
    tsl_increase_times = []
    profits_list = []

    buy_price = 0
    subsequent_buys = 0
    resulting_percentage = Decimal(100)

    last_buy = None
    sl_price = None
    tsl_active = False
    tsl_sell_price = None
    next_entry_price = None
    next_target_price = None
    tsl_increase_price = None
    tsl_activate_after = None

    strategy = entry_strategy.strategy_class(*entry_strategy.args)
    strategy.setUp(df)
    # Go through all the candlesticks
    for i in range(0, len(df['close'])-1):
        # Have we already opened a position?
        if last_buy is None:
            # If no, check whether the strategy is fulfilled at this point in time
            strategy_result = strategy.checkLongSignal(i)

            if strategy_result:
                # If strategy is fulfilled, buy the coin
                buy_price = exchange.toValidPrice(symbol, df['close'][i])
                buy_times.append([df['time'][i], buy_price])

                # Initialize TAKE PROFIT PRICE
                if exit_settings.pt is not None:
                    next_target_price = exchange.toValidPrice(symbol,\
                        buy_price * Decimal(exit_settings.pt), round_up=True)

                # Initialize STOP LOSS PRICE
                if exit_settings.sl is not None:
                    sl_price =  exchange.toValidPrice(symbol,\
                        buy_price * Decimal(exit_settings.sl))

                # Initialize TRAILING STOP LOSS PRICE
                if exit_settings.tsl is not None:
                    tsl_activate_after =  exchange.toValidPrice(symbol,\
                        buy_price * Decimal(exit_settings.tsl.after_profit))

                    if tsl_activate_after <= buy_price:
                        tsl_active = True
                        tsl_increase_price = buy_price
                        tsl_sell_price =  exchange.toValidPrice(symbol,\
                            buy_price * Decimal(exit_settings.tsl.value))

                # Initialize SUBSEQUENT ENTRY PRICE
                if entry_settings.se is not None:
                    next_entry_price = exchange.toValidPrice(symbol,\
                        buy_price * Decimal(entry_settings.se.after_profit))

                last_buy = {
                    "index": i,
                    "price": buy_price
                }

        elif last_buy is not None and i > last_buy["index"] + 1:
        # If we already opened a position, check whether the price has hit
        # either the stop loss price, tsl_price, the target price, or if a
        # subsequent entry is due

            ### TRAILING STOP LOSS LOGIC
            if exit_settings.tsl is not None:
                if not tsl_active:
                    if tsl_activate_after <= Decimal(df['high'][i]):
                        tsl_active_times.append((df['time'][i], tsl_activate_after))
                        tsl_active = True
                        tsl_increase_price = Decimal(df['high'][i])
                        tsl_sell_price = exchange.toValidPrice(symbol,\
                            Decimal(df['high'][i]) * Decimal(exit_settings.tsl.value))
                if tsl_active:
                    if Decimal(df['low'][i]) <= tsl_sell_price:
                    # Price went below TSL so we have to sell
                        profits_list.append(tsl_sell_price - last_buy['price'])
                        tsl_sell_times.append([df['time'][i], tsl_sell_price, subsequent_buys])
                        resulting_percentage = resulting_percentage * (tsl_sell_price / buy_price)
                        buy_price = Decimal(0)
                        tsl_active = False
                        tsl_activate_after = None
                        tsl_increase_price = None
                        last_buy = None
                        subsequent_buys = 0
                    elif Decimal(df['high'][i]) > tsl_increase_price:
                    # Price went above pervious high so we adjust TSL Target
                        tsl_increase_times.append((df['time'][i], tsl_increase_price))
                        tsl_increase_price = Decimal(df['high'][i])
                        tsl_sell_price = exchange.toValidPrice(symbol,\
                            Decimal(df['high'][i]) * Decimal(exit_settings.tsl.value))

            ### STOP LOSS LOGIC
            if exit_settings.sl is not None and \
                Decimal(df['low'][i]) < sl_price:
                # If price went below our stop_loss, it means we sold at that point
                profits_list.append(sl_price - last_buy['price'])
                sl_sell_times.append([df['time'][i], sl_price, subsequent_buys])
                resulting_percentage = resulting_percentage * (sl_price / buy_price)
                buy_price = Decimal(0)
                subsequent_buys = 0
                tsl_active = False
                tsl_activate_after = None
                tsl_increase_price = None
                last_buy = None

            ### SUBSEQUENT ENTRIES LOGIC
            if entry_settings.se is not None and \
                Decimal(df['low'][i]) < next_entry_price \
                and subsequent_buys < entry_settings.se.times:

                buy_price = next_entry_price

                if entry_settings.pt is not None:
                    next_target_price = exchange.toValidPrice(symbol,\
                        buy_price * Decimal(entry_settings.pt) * \
                        Decimal(entry_settings.se.pt_decrease), round_up=True)

                if exit_settings.tsl is not None:
                    tsl_activate_after = exchange.toValidPrice(symbol,\
                        buy_price * Decimal(exit_settings.tsl.after_profit))

                    if tsl_activate_after <= buy_price:
                        tsl_active = True
                        tsl_increase_price = buy_price
                        tsl_sell_price =  exchange.toValidPrice(symbol,\
                            buy_price * Decimal(exit_settings.tsl.value))
                    else:
                        tsl_active = False

                next_entry_price = exchange.toValidPrice(symbol,\
                    buy_price * Decimal(entry_settings.se.after_profit))
                
                buy_times.append([df['time'][i], buy_price])
                last_buy = { "index": i, "price": buy_price}
                subsequent_buys = subsequent_buys + 1

            ### TAKE PROFIT LOGIC
            if exit_settings.pt is not None and exit_settings.tsl is None and \
                Decimal(df['high'][i]) > next_target_price:

                tp_sell_times.append([df['time'][i], next_target_price, subsequent_buys])
                profits_list.append(next_target_price - last_buy['price'])
                resulting_percentage = resulting_percentage * \
                    (next_target_price / buy_price)
                tsl_increase_price = None
                last_buy = None
                subsequent_buys = 0
                tsl_active = False
                tsl_activate_after = None
                buy_price = Decimal(0)

    ms = df['time'][len(df['time'])-1] - df['time'][0]
    return dict(
        total_profit_loss = round(float(resulting_percentage), 2),
        buy_times = buy_times,
        tp_sell_times = tp_sell_times,
        sl_sell_times = sl_sell_times,
        tsl_sell_times = tsl_sell_times,
        tsl_active_times = tsl_active_times,
        tsl_increase_times = tsl_increase_times,
        profits_list = profits_list,
        start_time = df['time'][0],
        end_time = df['time'][len(df['time'])-1],
        seconds_of_backtesting = ms/1000,
        days_of_backtesting = round((ms/(1000 * 60 * 60 * 24)), 1)
    )