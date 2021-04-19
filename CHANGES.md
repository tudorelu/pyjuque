# CHANGES

## 0.1.1.7

### BUG FIXES
 - Fixed Backtester
 - Fixed bug that occured sometimes when exiting from signal 

## 0.1.1.6

### IMPROVEMENTS
 - Added ability to exit on [custom signal](./examples/Bot_CustomEntryExitStrategy.py#128). 


## 0.1.1.5

### IMPROVEMENTS
 - Backtester now returns lists with he entry and exit orders that can be passed directly to the plotter 

## 0.1.1.4

### FEATURES
 - simulation mode for Bot Runner (forward testing)
 -  exit on exit signals

### EXCHANGES
 - kucoin

### BUG FIXES
 - bot now stops placing orders when its (virtual) balance is insufficient