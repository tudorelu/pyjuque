# PYJUQUE
## Python Juju Quant Engine
### *AKA Another Crypto Trading Bot*

This project will implement the basic functionality needed to engage in algorithmic trading of cryptocurrencies on all major exchanges. It can be regarded as a starting point for more complex trading bots. It will implement

### Structure
Code is contained in `bot`. Tests are in `tests`.
# Features
## Plotting
There is some basic functionality for plotting in `bot/Plotter.py`

## Exchanges
At `bot/exchanges`. 

  - [Binance](/bot/Exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)

contains some tests

### Backtesting

Backtester infrastructure currently supports 
  - stop loss, trailing stop loss &
  - subsequent entries logic (DCA)

### Indicators
Started implementing the Indicators module which currently contains some indicators from `pyti`;.

The thinking is that this module should allow us to easily and quickly compute any of the hundreds of indicators out there and to use them in strategies & backtesting. Should seamlessly connect to the **Strategies** module.

### Strategies (EXPERIMENTAL)

A base module which allows us to define buying & selling strategies for crypto assets. The design behind a strategy still needs some work, but generally each strategy will contain the following phases: `setup` (where the indicators are computed), `getIndicators` (to be used for plotting), `checkBuySignal`, `checkSellSignal`, `getBuySignalsList` and `getSellSignalsList` (the last two to be used for backtesting). Check other trading bots on how they think their strategies.

Currently contains two basic strategies. More strategies will be added together with a **build-your-own** strategy template. Should seamlessly connect to the **Backtesting** & **Order Management** modules.

### Tests
Run them with the command `nose2`

## **Coming Soon**

### Order Management
A module which will handle the buying and selling of assets, given simple or more advanced rules, allowing us to run a strategy indefinitely. Features:
- Placing market, limit & OCO orders
- Trading on signals
- Trading below/above signal by some %
- Stop loss & Trailing stop loss
- Multiple trade entries (in case trade goes against you)

### State persistence 
The ability to save the current bot state for later use. We may use something like SQLAlchemy to easily port to multiple SQL based DBs, but also want to have an API for transforming data to JSON.

### More Exchanges

Binance Futures, Bitmex, Bitfinex, FTX, Bybit.

## **Coming Later**

Margin Trading, Market Making, Hyper Parameter Tuning.

# Contributing

### Adding new Exchanges
Each exchange should extend the BaseExchange class and implement all functions there. 
