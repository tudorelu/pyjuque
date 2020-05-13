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

  - [Binance](/bot/exchanges/Binance.py) - based on the official [REST API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)

## **Coming Soon**

### Backtesting

### Indicators
Will implement an Indicators module which allows us to easily compute any of the hundreds of indicators out there and use them in strategies & backtesting. Should seamlessly connect to the **Strategies** module.

Possibly will use TA-lib & pyti libs, together with custom indicators.

### Strategies
A base module which allows us to define buying & selling strategies for crypto assets.

Will contain a few basic strategies together with a **build-your-own** strategy template. Should seamlessly connect to the **Backtesting** & **Order Management** modules.

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
