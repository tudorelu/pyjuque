# PYJUQUE
## Python Juju Quant Engine
### *AKA Private Crypto Trading Bot - Don't give away your strategies! *

This project implements some basic functionality needed to engage in algorithmic trading of cryptocurrencies. It can be regarded as a starting point for more complex trading bots, which implements / will implement the following features:

### Structure
Code is contained in `bot`. Tests are in `tests`.
# Features
## Plotting
There is some basic functionality for plotting in `bot/Plotter.py`

## Exchanges
At `bot/Exchanges`. 

  - [Binance](/bot/Exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)

contains some tests

### Backtesting
At `bot/Engine/Backtester.py`. 

Backtester infrastructure currently supports 
  - stop loss, trailing stop loss &
  - subsequent entries logic (DCA)

### Indicators
At `bot/Indicators.py`. 

Started implementing the Indicators module which currently contains some indicators from `pyti`;.

The thinking is that this module should allow us to easily and quickly compute any of the hundreds of indicators out there and to use them in strategies & backtesting. Should seamlessly connect to the **Strategies** module.

### Strategies
At `bot/Strategies`. 

A base module which allows us to define buying & selling strategies for crypto assets. Each strategy will contain the following phases: 
`setup` (where the indicators are computed), 
`getIndicators` (to be used for plotting), 
`checkBuySignal`, `checkSellSignal`, 
`getBuySignalsList` and `getSellSignalsList` (the last two to be used for backtesting). 

Currently contains a few basic strategies. More strategies will be added together with a **build-your-own** strategy template. Should seamlessly connect to the **Backtesting** & **Order Management** modules.


### Strategy Optimiser 
At `bot/Strategies/StrategyOptimiser.py`. 

Currently allows for optimising strategy parameters using a genetic algorithm.

### Tests
Run them with the command `nose2`

## **In Progress**

### Order Management
At `bot/Engine/OrderManagement.py`. 

A module which will handle the buying and selling of assets, given simple or more advanced rules, allowing us to run a strategy indefinitely. 

##### Current Features:
- Placing Entry (Buy) Orders on Signal 
- Placing Exit Order when Entry Order was fulfilled

##### Future Features: 
- Market & OCO orders
- Selling on signals
- Trading below/above signal by some %
- Stop loss & Trailing stop loss
- Multiple trade entries (in case trade goes against you)

### State persistence 
The ability to save the current bot state for later use. We may use something like SQLAlchemy to easily port to multiple SQL based DBs, but also want to have an API for transforming data to JSON.


## **Coming Soon**
### More Exchanges
Binance Futures, Bitmex, Bitfinex, FTX, Bybit.
Margin Trading, Market Making, Hyper Parameter Tuning.

# Contributing
To contribute simply fork the repo, write your desired feature in your own fork and make a pull request upon finishing. Please write tests!

### Adding new Exchanges
Each exchange should extend the BaseExchange class and implement all functions there. 
