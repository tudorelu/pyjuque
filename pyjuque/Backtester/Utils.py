
from dataclasses import dataclass, field
from decimal import Decimal
from pyjuque.Strategies import Strategy
from numpy import float64

# # This is necessary because Apple M1 sillicon doesn't support float128 yet
try:
    from numpy import float128
except ImportError:
    from numpy import longdouble as float128

# # Alternative solution: use cpuinfo to check if using M1 
# import cpuinfo
# info = cpuinfo.get_cpu_info()
# if 'Apple' in info['brand_raw']:
#     from numpy import longdouble as float128
# else:
#     from numpy import float128


@dataclass(frozen=True)
class BacktesterConfig:
    strategy_class:Strategy
    strategy_params:dict = field(default_factory=dict)
    symbol:str = field(default=None)
    timeframe:str = field(default=None)
    trade_amount:int or float or Decimal = field(default=1.0)
    use_base_amount:bool = field(default=False)
    fee_percent:int or float or Decimal = field(default=0.1)
    stop_loss_value:int or float or Decimal = field(default=None)
    take_profit_value:int or float or Decimal = field(default=None)
    stop_loss_type:str = field(default='percent')   # 'fixed' or 'percent'
    take_profit_type:str = field(default='percent')   # 'fixed' or 'percent'
    trailing_stop_loss:bool = field(default=False)
    go_long:bool = field(default=False)
    go_short:bool = field(default=False)
    exit_on_long:bool = field(default=False)
    exit_on_short:bool = field(default=False)
    reinvest:bool = field(default=False)


    def __post_init__(self):
        """ Do some type and value checking here. """
        for bool_type in [self.use_base_amount, self.trailing_stop_loss,
            self.go_long, self.go_short, self.exit_on_long, 
            self.exit_on_short, self.reinvest]:
            if type(bool_type) is not bool and bool_type is not None:
                raise TypeError(f'Field {bool_type} must be of type "bool"')

        for str_type in [self.symbol, self.timeframe]:
            if type(str_type) is not str and str_type is not None:
                raise TypeError('Fields "symbol" and "timeframe" must be of '
                    'type "str", not {type(num_type)}')

        for num_type in [self.trade_amount, self.fee_percent,  
            self.stop_loss_value, self.take_profit_value]:
            if num_type is not None and type(num_type) not in \
                [Decimal, float, int, float64, float128]:
                raise TypeError(f'Fields "trade_amount", "fee_percent", ' 
                    '"stop_loss_value", "take_profit_value" must be either '
                    'of type "int", "float" or "Decimal", "np.float64" ' 
                    f'or "np.float128", not {type(num_type)}')

        for pct_type in [self.fee_percent, self.stop_loss_value, 
                                    self.take_profit_value]:
            if pct_type is not None and (pct_type < 0):
                raise ValueError('Fields "fee_percent", "stop_loss_value" '
                    'and "take_profit_value" must be above 0.')

        for pct_type in [self.fee_percent]:
            if pct_type is not None and (pct_type >= 100):
                raise ValueError('Fields "fee_percent" '
                    'must be below 100.')
        for pct_type in [self.stop_loss_type, 
                                    self.take_profit_type]:
            if pct_type is not None and pct_type not in ['fixed', 'percent']:
                raise ValueError('Fields "stop_loss_type" and '
                '"take_profit_type" must be equal to "fixed" or "percent"')

        for not_none in [self.trade_amount]:
            if not_none is None:
                raise ValueError('Field "trade_amount" must not be None')

        if self.go_short is not True and self.go_long is not True:
            raise ValueError('At least one of "go_long", "go_short" should be True')
        
        if self.go_long is True and self.go_short is False:
            if self.exit_on_short is not True and self.take_profit_value is None \
                and self.stop_loss_value is None:
                raise ValueError('When "go_long" is True and "go_short" False, '
                    'either "exit_on_short" should be set to True, or either '
                    '"take_profit_value" or "stop_loss_value" should be set. '
                    'Otherwise we have no way to exit trades')

        if self.go_long is False and self.go_short is True:
            if self.exit_on_long is not True and self.take_profit_value is None \
                and self.stop_loss_value is None:
                raise ValueError('When "go_short" is True and "go_long" False, '
                    'either "exit_on_long" should be set to True, or either '
                    '"take_profit_value" or "stop_loss_value" should be set.'
                    'Otherwise we have no way to exit trades')

        # Force conversion to decimal
        # if self.trade_amount != None:
        #     self.trade_amount = Decimal(self.trade_amount)
        # if self.fee_percent != None:
        #     self.fee_percent = Decimal(self.fee_percent)


@dataclass
class BacktesterResults:
    used_config:BacktesterConfig
    timestamp_start:int
    timestamp_end:int
    total_candles:int
    #### For all trades
    n_trades:int
    n_wins:int
    n_losses:int
    gross_profit:float or Decimal               # total profit, without subtracting the losses
    gross_loss:float or Decimal                 # total loss, without subtracting the profits
    net_profit:float or Decimal                 # net profit (profit_gross - loss_gross)
    profit_factor:float or Decimal              # gross_profit / gross_loss
    pnl_ratio:float or Decimal                  # final balance / initial balance
    fees_paid:float or Decimal
    winrate:float or Decimal                    # n_wins / n_trades
    #### For longs only
    n_longs:int
    gross_profit_longs:float or Decimal         # total profit of long trades
    gross_loss_longs:float or Decimal           # total loss of long trades
    net_profit_longs:float or Decimal           # net profit of long trades (profit_longs - loss_longs)
    profit_factor_longs:float or Decimal        # gross_profit_longs / gross_loss_longs
    #### For shorts only
    n_shorts:int
    gross_profit_shorts:float or Decimal        # total profit of short trades
    gross_loss_shorts:float or Decimal          # total loss of short trades
    net_profit_shorts:float or Decimal          # net profit of short trades (profit_shorts - loss_shorts)
    profit_factor_shorts:float or Decimal       # gross_profit_shorts / gross_loss_shorts
    # For all trades
    max_equity:float or Decimal
    max_drawdown:float or Decimal
    average_drawdown_duration:int
    average_trade_duration:int
    average_trade_profit:float or Decimal
    longest_drawdown_duration:int                 # number of candles for the longest period being in dd
    longest_trade_duration:int
