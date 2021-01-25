## **Py**thon **Ju**ju **Qu**ant **E**ngine
**PYJUQUE**   &nbsp; &nbsp;  *(pai-jook)*
*(**Py**-thon **Ju**-ju **Qu**-ant **E**-ngine)*

This project implements the basic functionality required to engage in algorithmic trading. It can be regarded as a starting point for more complex trading bots.

## Getting Started
Make sure you have pip installed. Run:
```sh
# To install all the requirements
pip install -r requirements.txt
```

Add a .env file in the root filepath, then populate it with the following lines. Checkout this [example .env file](/.env.example)

```
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

You should be good to go! Check out the example section. 

## Features
This library implements the following features:

### Bot Controller
At `pyjuque/Engine/BotController.py`. 

A module which handles the buying and selling of assets, given simple or more advanced rules, allowing us to run a strategy indefinitely. Checkout this [example](/examples/TryUniversalBotController.py).

##### Current Features:
- Placing Entry (Buy) Orders on Signal 
- Market, Limit & Stop Loss orders 
- Placing Exit Order when Entry Order was fulfilled
- Trading below/above signal by some %

##### Future Features: 
- OCO orders
- Selling on signals
- Trailing stop loss
- Multiple trade entries (in case trade goes against you)

State persistence Using SQLAlchemy.


### Backtesting
At `pyjuque/Engine/Backtester`. 

Backtester infrastructure currently supports:
  - stop loss, trailing stop loss
  - subsequent entries logic (as if Dollar Cost Averaging is enabled)

<!-- Checkout this [example](/examples/try_backtester.py). -->

### Plotting
There is some basic functionality for plotting in `pyjuque/Plotting`

### Exchange Connectors

Implementing multiple exchanges with [ccxt](https://github.com/ccxt/ccxt). Check out implementation at [CcxtExchange](/pyjuque/Exchanges/CcxtExchange.py). Currently implemented:

binance
okex

***Older:***
 
At `pyjuque/Exchanges`. 

  - [Binance](/pyjuque/Exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)


<!-- ### Strategy Optimiser 
At `pyjuque/Strategies/StrategyOptimiser.py`. 

Currently allows for optimising strategy parameters using a genetic algorithm. Checkout this [example](/examples/try_strategy_optimiser.py). -->

### Local Order Book (for Binance)
At `pyjuque/Exchanges/BinanceOrderBook.py`. 

Creates and stores a local order book for the specified symbols. Order Book is updated every second through a websocket connection to the Exchange (currently Binance). Checkout this [example](/examples/try_local_order_book.py).

```py
from pyjuque.Exchanges.BinanceOrderBook import OrderBook

# Initialize & start OrderBook with desired symbols
ob = OrderBook(symbols=['BTCUSDT', 'LTCUSDT'])
ob.startOrderBook()
...
# Get Updated Order Book data at any point in your code 
ordb = ob.getOrderBook()
print(ordb)

{
  'BTCUSDT': {
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
  'LTCUSDT': {
      'asks': [ ... ],
      'bids': [ ... ],
      'lastUpdateId': 1521585540  # ignore this
  },
 'counter': 11                    # ignore this
}

```

### Tests
Run them with the command `nose2`

## **Coming Soon**
### More Exchanges
Binance Futures, Bitmex, Bitfinex, FTX, Bybit.
Margin Trading, Market Making, Hyper Parameter Tuning.

# Contributing
To contribute simply fork the repo, write your desired feature in your own fork and make a pull request upon finishing. Writing tests is also appreciated.

### Adding new Exchanges
Each exchange should extend the BaseExchange class and implement all functions there. 
