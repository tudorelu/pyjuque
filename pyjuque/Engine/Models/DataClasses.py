
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class BotType(Enum):
    """
    Enum for bot type
    """
    GRID = "grid"
    RULE = "rule"

@dataclass
class Bot:
    """
    Base class for all bots
    """
    id: int
    name: str
    symbol: str
    base_asset: str
    quote_asset: str
    base_balance: Decimal
    quote_balance: Decimal
    trade_amount: Decimal
    bot_type: BotType
    exchange_creds_id: str
    entry_settings_id: str
    exit_settings_id: str