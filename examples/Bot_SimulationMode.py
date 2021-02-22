
# Imports for the strategy
import pandas_ta as ta

# Importing these to be able to run this example 
# from the main pyjuque folder
from os import getenv
from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)

# Import for defining the bot
from pyjuque.Bot import defineBot
# Import for defining the Strategy
from pyjuque.Strategies import StrategyTemplate
from pyjuque.Exchanges.CcxtExchange import CcxtExchange
from pprint import pprint
import time

## Defines the strategy
class EMACross(StrategyTemplate):
    """ Bollinger Bands x RSI """
    minimum_period = 100
    def __init__(self, fast_ma_len = 10, slow_ma_len = 50):
        self.fast_ma_len = fast_ma_len
        self.slow_ma_len = slow_ma_len
        # the minimum number of candles needed to compute our indicators
        self.minimum_period = max(100, slow_ma_len)


    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df):
        df['slow_ma'] = ta.ema(df['close'], self.slow_ma_len)
        df['fast_ma'] = ta.ema(df['close'], self.fast_ma_len)
        self.dataframe = df


    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place an order
    def checkLongSignal(self, i = None):
        """ """
        df = self.dataframe
        if i == None:
            i = len(df) - 1
        if i < 1:
            return False
        if df['low'][i-1] < df['slow_ma'][i-1] and df['low'][i] > df['slow_ma'][i] \
            and df['low'][i] > df['fast_ma'][i] and df['fast_ma'][i] > df['slow_ma'][i]:
            return True
        return False


    def checkShortSignal(self, i = None):
        df = self.dataframe
        if i == None:
            i = len(df) - 1
        if i < 1:
            return False
        if (df['low'][i-1] > df['slow_ma'][i-1] or df['fast_ma'][i-1] > df['slow_ma'][i-1] ) \
            and df['close'][i] < df['slow_ma'][i] and df['close'][i] < df['fast_ma'][i] \
            and df['fast_ma'][i] < df['slow_ma'][i]:
            return True
        return False


bot_config = {
    'name' : 'my_kucoin_bot_testing',
    'test_run' : True,
    'exchange' : {
        'name' : 'kucoin',
        'params' : {
            # 'api_key': getenv('KUCOIN_API_KEY'),
            # 'secret' : getenv('KUCOIN_API_SECRET'),
            # 'password' : getenv('KUCOIN_PASSWORD'),
        },
    },
    'symbols' : ['SNX/USDT', 'XLM/USDT', 'VET/USDT', 'GO/USDT', 'EOS/USDT', 'ETC/USDT', 'LTC/USDT', 
        'NANO/USDT', 'LYM/USDT', 'TKY/USDT', 'ONT/USDT', 'AOA/USDT', 'SUSD/USDT', 'TRX/USDT', 'BSV/USDT', 
        'KCS/USDT', 'NEO/USDT', 'BCH/USDT', 'ETH/USDT', 'BTC/USDT', 'AVA/USDT', 'MHC/USDT', 'MTV/USDT', 
        'TEL/USDT', 'ATOM/USDT', 'ETN/USDT', 'TOMO/USDT', 'VSYS/USDT', 'CHR/USDT', 'COTI/USDT', 'BNB/USDT', 
        'JAR/USDT', 'ALGO/USDT', 'XEM/USDT', 'CIX100/USDT', 'XTZ/USDT', 'ZEC/USDT', 'ADA/USDT', 'R/USDT', 
        'WXT/USDT', 'FORESTPLUS/USDT', 'BOLT/USDT', 'ARPA/USDT', 'SERO/USDT', 'DAPPT/USDT', 'NOIA/USDT', 
        'BLOC/USDT', 'WIN/USDT', 'DERO/USDT', 'BTT/USDT', 'EOSC/USDT', 'ENQ/USDT', 'ONE/USDT', 'TOKO/USDT', 
        'VID/USDT', 'LUNA/USDT', 'SDT/USDT', 'MXW/USDT', 'SXP/USDT', 'AKRO/USDT', 'MAP/USDT', 'AMPL/USDT', 
        'DAG/USDT', 'POL/USDT', 'ARX/USDT', 'NWC/USDT', 'BEPRO/USDT', 'VRA/USDT', 'KSM/USDT', 'XNS/USDT', 
        'DASH/USDT', 'ROAD/USDT', 'PMGT/USDT', 'SUTER/USDT', 'ACOIN/USDT', 'SENSO/USDT', 'XDB/USDT', 'SYLO/USDT', 
        'WOM/USDT', 'DGB/USDT', 'LYXE/USDT', 'STX/USDT', 'USDN/USDT', 'XSR/USDT', 'COMP/USDT', 'CRO/USDT', 
        'KAI/USDT', 'WEST/USDT', 'WAVES/USDT', 'ORN/USDT', 'BNS/USDT', 'MKR/USDT', 'MLK/USDT', 'JST/USDT', 
        'SUKU/USDT', 'DIA/USDT', 'LINK/USDT', 'DMG/USDT', 'DOT/USDT', 'SHA/USDT', 'EWT/USDT', 'USDJ/USDT', 
        'CKB/USDT', 'UMA/USDT', 'ALEPH/USDT', 'VELO/USDT', 'SUN/USDT', 'BUY/USDT', 'YFI/USDT', 'LOKI/USDT', 
        'UNI/USDT', 'UOS/USDT', 'NIM/USDT', 'DEGO/USDT', 'RFUEL/USDT', 'FIL/USDT', 'REAP/USDT', 'AAVE/USDT', 
        'PRE/USDT', 'COMB/USDT', 'SHR/USDT', 'VIDT/USDT', 'UBXT/USDT', 'BCHA/USDT', 'ROSE/USDT', 'USDC/USDT', 
        'CTI/USDT', 'XHV/USDT', 'PLU/USDT', 'GRT/USDT', 'CAS/USDT', 'MSWAP/USDT', 'GOM2/USDT', 'REVV/USDT', 
        'LON/USDT', '1INCH/USDT', 'LOC/USDT', 'API3/USDT', 'UNFI/USDT', 'HTR/USDT', 'FRONT/USDT', 'MIR/USDT', 
        'HYDRA/USDT', 'DFI/USDT', 'CRV/USDT', 'SUSHI/USDT', 'FRM/USDT', 'PROPS/USDT', 'ZEN/USDT', 'CUDOS/USDT', 
        'REN/USDT', 'LRC/USDT', 'KLV/USDT', 'BOA/USDT', 'THETA/USDT', 'QNT/USDT', 'BAT/USDT', 'DOGE/USDT', 
        'DAO/USDT', 'STRONG/USDT', 'TRIAS/USDT', 'MITX/USDT', 'CAKE/USDT', 'KAT/USDT', 'XRP/USDT', 'GRIN/USDT'],
    'starting_balance' : 100,
    'strategy': {
        'class': EMACross,
        'params': {
            'fast_ma_len' : 8, 
            'slow_ma_len' : 30, 
        }
    },
    'timeframe' : '1m',
    'entry_settings' : {
        'initial_entry_allocation': 10,
        'signal_distance': 0.3,
        'leverage': 1,
    },
    'exit_settings' : {
        'take_profit' : 10,
        'stop_loss_value': 20,
        'exit_on_signal': True
    }
}

## Runs the bot in an infinite loop, stoppable from the terminal with CTRL + C
def Main():
    # The following will run the strategy on the exchange
    bot_controller = defineBot(bot_config)
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        time.sleep(60)

if __name__ == '__main__':
    Main()
