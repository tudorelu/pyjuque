## **Py**thon **Ju**ju **Qu**ant **E**ngine
**PYJUQUE**   &nbsp; &nbsp;  *(pai-jook)*
*(**Py**-thon **Ju**-ju **Qu**-ant **E**-ngine)*

This project implements the basic functionality required to engage in algorithmic trading. It can be regarded as a starting point for more complex trading bots, which implements the following features:

### Structure
Code is contained in `pyjuque`. Tests are in `tests`.
## Features
### Plotting
There is some basic functionality for plotting in `pyjuque/Plotter`

### Exchanges
At `pyjuque/Exchanges`. 

  - [Binance](/pyjuque/Exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)

### Backtesting
At `pyjuque/Engine/Backtester`. 

Backtester infrastructure currently supports:
  - stop loss, trailing stop loss
  - subsequent entries logic (backtest as if Dollar Cost Averaging is enabled)

Checkout this [example](/examples/try_backtester.py).

### Indicators
At `pyjuque/Indicators`. 

Started implementing the Indicators module which currently contains some indicators from `pyti`;.

The thinking is that this module should allow us to easily and quickly compute any of the hundreds of indicators out there and to use them in strategies & backtesting. Should seamlessly connect to the **Strategies** module.

### Strategies
At `pyjuque/Strategies`. 

A base module which allows us to define buying & selling strategies for crypto assets. Each strategy will contain the following phases: 
`setup` (where the indicators are computed), 
`getIndicators` (to be used for plotting), 
`checkBuySignal`, `checkSellSignal`, 
`getBuySignalsList` and `getSellSignalsList` (the last two to be used for backtesting). 

Currently contains a few basic strategies. More strategies will be added together with a **build-your-own** strategy template. Should seamlessly connect to the **Backtesting** & **Bot Controller** modules.


### Strategy Optimiser 
At `pyjuque/Strategies/StrategyOptimiser.py`. 

Currently allows for optimising strategy parameters using a genetic algorithm. Checkout this [example](/examples/try_strategy_optimiser.py).

### Local Order Book
At `pyjuque/Engine/OrderBook.py`. 

Creates and stores a local order book for the specified symbols. Order Book is updated every second through a websocket connection to the Exchange (currently Binance). Checkout this [example](/examples/try_local_order_book.py).

```py
from pyjuque.Engine.OrderBook import OrderBook

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

## **In Progress**

### Bot Controller
At `pyjuque/Engine/BotController.py`. 

A module which will handle the buying and selling of assets, given simple or more advanced rules, allowing us to run a strategy indefinitely. Checkout this [example](/examples/try_BotController.py).

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

### State persistence 

Using SQLAlchemy.


## **Coming Soon**
### More Exchanges
Binance Futures, Bitmex, Bitfinex, FTX, Bybit.
Margin Trading, Market Making, Hyper Parameter Tuning.

# Contributing
To contribute simply fork the repo, write your desired feature in your own fork and make a pull request upon finishing. Please write tests!

### Adding new Exchanges
Each exchange should extend the BaseExchange class and implement all functions there. 
