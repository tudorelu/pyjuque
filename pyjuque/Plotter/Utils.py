
from dataclasses import dataclass, field
from numpy import array

@dataclass
class GraphDetails:
    name:str
    xsource:str or list or array = field(default='time', repr=False)
    ysource:bool or list or array = field(default=None, repr=False)
    xaxis:str = field(default='x')
    yaxis:str = field(default='y')
    type:str = field(default='scatter')
    mode:str = field(default='lines')
    color:str = field(default=None)
    marker_size:int = field(default=15)
    marker_symbol:str = field(default=None)
    showlegend:bool = field(default=True)
    width:int = field(default=300_000)
    extra_kwargs:dict = field(default_factory=dict, repr=False)


import math
def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor
