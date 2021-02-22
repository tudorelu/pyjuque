## **Py**thon **Ju**ju **Qu**ant **E**ngine
**PYJUQUE**   &nbsp; &nbsp;  *(pai-jook)*
*(**Py**-thon **Ju**-ju **Qu**-ant **E**-ngine)*

This project implements the basic functionality required to engage in algorithmic trading. It can be regarded as a starting point for more complex trading bots.

## Installation
Make sure you have pip installed. Run:

```sh
pip install pyjuque
```

You should be good to go! Check out the example section. 

## Getting Started

Checkout these examples to get started stratght away: [strategy 1](/examples/Bot_CustomStrategy.py), [strategy 2](/examples/Bot_StrategyFromTemplate.py). Below is the simplest example of how to get started with pyjuque. Read the next section to understand the thinking behind it.

```py
from pyjuque.Bot import defineBot
import time

def customEntryStrategy(bot_controller, symbol):
    # signal = will_moon(symbol)          # bool
    # last_price = get_price(symbol)      # float
    return signal, last_price

## Defines the overall configuration of the bot 
bot_config = {
    'name' : 'my_bot',
    'test_run' : False                    # set to True to run in simulation mode
    'exchange' : {
        'name' : 'binance',
        'params' : {                      # put here any param that ccxt accepts
            'api_key': 'YOUR_API_KEY',
            'secret' : 'YOUR_API_SECRET'
        },
    },
    'symbols' : ['LINK/BTC', 'ETH/BTC'],  # !! all symbols must trade against same coin
                                          # !! IE: [XX/BTC, YY/BTC] OR [AA/EUR, CC/EUR]
    'starting_balance' : 0.0005,          # denominated in the quote asset against which 
                                          # the symbols are trading (BTC in this case)
    'strategy': {
        'custom': True,
        'entry_function': customEntryStrategy,
    },
    'entry_settings' : {
        'initial_entry_allocation': 100,  # 100% of starting_balance goes in every trade
        'signal_distance': 0.3            # upon receiving an entry_signal, entry order
                                          # is placed 0.3% away from market price
    },
    'exit_settings' : {
        'take_profit' : 3,                # take profit 3% above entry orders
        'stop_loss_value': 10             # stop loss 10% below entry orders
    },
}


## Runs the bot in an infinite loop that executes every 60 seconds 
## stoppable from the terminal with CTRL + C
def Main():
    bot_controller = defineBot(bot_config)
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        time.sleep(60)


if __name__ == '__main__':
    Main()
```

## Run a Simple Bot

The idea behind this library is to allow you to implement whatever trading strategy you want, without having to worry about how to connect to the different exchanges via apis, or how to place, cancel and keep track of orders. You simply provide the signals and pyjuque does the rest. 

There are a number of settings that you define, like what symbols to trade on, how much money to place per trade and what exchange to use. You also get to set exit settings such as a take profit value and a stop loss value. All these settings get specified in a config dict. Below is a complete example of a config dict:

```py
## Defines the overall configuration of the bot 
bot_config = {
    # Name of the bot, as stored in the database
    'name' : 'my_bot',

    # exchange information (fill with your api key and secret)
    'exchange' : {
        'name' : 'binance', # or 'okex'
        'params' : {  # any parameter accepted by ccxt can go here
            'api_key': 'your_api_key_here',
            'secret' : 'your_secret_here',
            # 'password' : 'your_password_here' # if using 'okex'
        },
    },

    # starting balance for bot
    'starting_balance' : 0.0005,

    # symbols to trade on
    # !IMPORTANT! all symbols must trade against the same coin
    # !! IE: [AAA/BTC, BBB/BTC] OR [AAA/USDT, CCC/USDT]
    'symbols' : ['LINK/BTC', 'ETH/BTC'],  

    # strategy class / function (here we define the entry and exit strategies.)
    # this bot places an entry order when 'customEntryFunction' retruns true
    'strategy': { 
       'custom': True,
       'entry_function' : customEntryFunction 
    },

    # when the bot receives the buy signal, the order is placed according 
    # to the settings specified below
    'entry_settings' : {

        # between 0 and 100, the % of the starting_balance to put in an order
        'initial_entry_allocation': 100,

        # number between 0 and 100 - 1% means that when we get a buy signal, 
        # we place buy order 1% below current price. if 0, we place a market 
        # order immediately upon receiving signal
        'signal_distance': 0.3
    },

    # This bot exits when our filled orders have reached a take_profit % above 
    # the buy price, or a stop_loss_value % below it
    'exit_settings' : {

        # take profit value between 0 and infinity, 3% means we place our sell 
        # orders 3% above the prices that our buy orders filled at
        'take_profit' : 3,

        # stop loss value in percent - 10% means stop loss at 10% below our 
        # buy order's filled price
        'stop_loss_value': 10
    },
}
```

Besides these settings, you need to provide an entry strategy. It can be as simple as a function, or a more complex strategy class. We'll go over the simple example:

```py

# This is our signal function.
# It receives two parameters - the bot_controller,
# which gives us access to the exchange and to the 
# database, and the symbol on which the bot is 
# currently checking entry signals.
#
# It must return two values, a boolean and a number.
# The boolean is the signal, and the number is the 
# latest price of that symbol 
#
def customEntryFunction(bot_controller, symbol):
  # ... do some stuff here ...
  return signal, last_price_of_symbol

```

The beauty of this is that you can do whatever the heck you want in that custom entry function, because as long as you return a symbol and the latest price, pyjuque will be happy. You can check coins prices and their indicators, the volume on multiple exchanges, different order books, even weather data, twitter feeds or astronomical events. 

Here's a complete example of how to get started with pyjuque:

```py

from pyjuque.Bot import defineBot

## This is our signal function for now. 
def customEntryFunction(bot_controller, symbol):
  # ... do some stuff here ...
  return signal, last_price

## Defines the overall configuration of the bot 
bot_config = { ... }

## Runs the bot in an infinite loop, stoppable 
## from the terminal with CTRL + C
def Main():
    bot_controller = defineBot(bot_config)
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        time.sleep(60)


if __name__ == '__main__':
    Main()
```

Upon creating the bot, a database will be created in your computer, keeping track of orders placed. You can run this example and it will work - but you should update customEntryFunction to do some calculations & return true sometimes, because in its current state the bot won't ever make any trades.

Checkout these examples for more info: [strategy 1](/examples/Bot_CustomStrategy.py), [strategy 2](/examples/Bot_StrategyFromTemplate.py).

## Features


##### Current Features:
- Long Bot (Placing Buy Orders on Custom Signals)
  - Market, Limit & Stop Loss Orders 
  - Automatically Placing Exit Order when Entry Order was fulfilled
  - State Persistance, the bot stores trades locally
- Binance Local Order Book 
- Plotting Capabilities
- Simple Defiinitian of Entry Strategy & Exit Rules (via bot_config)
- State Persistence Using SQLAlchemy, for any flavour of SQL

##### In Development:
- Grid Bot

##### Future Features: 
- Short Bot
- OCO orders
- Selling on signals
- Trailing Stop Loss
- Multiple Entries


## Modules
This library implements the following modules:

### Bot Controller
At `pyjuque/Engine/BotController.py`. 

A module which handles the buying and selling of assets, given simple or more advanced rules, allowing us to run a strategy indefinitely. 

Through the bot controller you can access the following objects
 - [bot_controller.exchange](/pyjuque/Exchanges/CcxtExchange.py) 
    - bot_controller.exchange has some methods that are used under the hood by pyjquue, like 
        - getOHLCV
        - placeLimitOrder 
        - placeMarketOrder
        - etc
 - **bot_controller.exchange.ccxt**, a [ccxt](https://github.com/ccxt/ccxt) object which uses the credentials you provided in the bot_config 
 - **bot_controller.session**, SQLAlchemy session through which you can query the database 
 - [**bot_controller.bot model**](/pyjuque/Engine/Models/BotModels.py#L89), the model of the bot as stored in the db
 - **bot_controller.status_printer**, a [yaspin](https://github.com/pavdmyt/yaspin) spinner used for logging

You can also access the following functions
  - **bot_controller.executeBot()**, which goes through a bot loop of:
    - checking signals on symbols and placing orders if signals are true
    - checking all open orders placed by the bot and updating them, like so: 
        - if a buy order was filled it places the subsequent exit order, at a take_profit price above the buy price
        - if the current price is below stop_loss_value for an open buy order, exits using market price
  - **bot_controller.log()** which allows you to print some stuff to the terminal
  - **bot_controller.bot_model.getOrders(bot_controller.session)** which allows you to get all orders
  - **bot_controller.bot_model.getOpenOrders(bot_controller.session)** which allows you to get all open orders
  
### Exchange Connectors

Implementing multiple exchanges with [ccxt](https://github.com/ccxt/ccxt). Check out implementation at [CcxtExchange](/pyjuque/Exchanges/CcxtExchange.py). Currently implemented:

binance
okex

***Older (Deprecated):***
 
At `pyjuque/Exchanges`. 

  - [Binance](/pyjuque/Exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)


<!-- ### Strategy Optimiser 
At `pyjuque/Strategies/StrategyOptimiser.py`. 

Currently allows for optimising strategy parameters using a genetic algorithm. Checkout this [example](/examples/try_strategy_optimiser.py). -->

### Local Order Book (for Binance)
At `pyjuque/Exchanges/BinanceOrderBook.py`. 

Creates and stores a local order book for the specified symbols. Order Book is updated every second through a websocket connection to the Exchange (currently Binance). Checkout this [example](/examples/Feature_BinanceLocalOrderBook.py).

```py
from pyjuque.Exchanges.BinanceOrderBook import OrderBook

# Initialize & start OrderBook with desired symbols
ob = OrderBook(symbols=['BTC/USDT', 'LTC/USDT'])
ob.startOrderBook()
...
# Get Updated Order Book data at any point in your code 
ordb = ob.getOrderBook()
print(ordb)

{
  'BTC/USDT': {
      'asks': [
          ['13662.31000000', '3.24473100'],
          ['13662.82000000', '0.06815300'],
          ['13663.08000000', '0.00900000'],
          ...
          ['20000.00000000', '95.22325900']
        ],
      'bids': [
          ['13662.30000000', '1.26362900'],
          ['13661.78000000', '0.04395000'],
          ['13661.62000000', '0.01439200'],
          ...
          ['10188.00000000', '1.11546400']
        ],
      'lastUpdateId': 6382686192  # ignore this
  },
  'LTC/USDT': {
      'asks': [ ... ],
      'bids': [ ... ],
      'lastUpdateId': 1521585540  # ignore this
  },
 'counter': 11                    # ignore this
}

```

## **Coming Soon**
### More Exchanges
Binance Futures, Bitmex, Bitfinex, FTX, Bybit.
Margin Trading, Market Making, Hyper Parameter Tuning.

# Contributing
To contribute simply fork the repo, write your desired feature in your own fork and make a pull request upon finishing. Writing tests is also appreciated.

