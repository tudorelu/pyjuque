
import sqlalchemy.types as types
from decimal import Decimal


class SqliteDecimal(types.TypeDecorator):
  # This TypeDecorator use Sqlalchemy Integer as impl. It converts Decimals
  # from Python to Integers which is later stored in Sqlite database.
  impl = types.BigInteger

  def __init__(self, scale):
    # It takes a 'scale' parameter, which specifies the number of digits
    # to the right of the decimal point of the number in the column.
    types.TypeDecorator.__init__(self)
    self.scale = scale
    self.multiplier_int = 10 ** self.scale

  def process_bind_param(self, value, dialect):
    # e.g. value = Column(SqliteDecimal(2)) means a value such as
    # Decimal('12.34') will be converted to 1234 in Sqlite
    if value is not None:
      value = int(Decimal(value) * self.multiplier_int)
    return value

  def process_result_value(self, value, dialect):
    # e.g. Integer 1234 in Sqlite will be converted to SqliteDecimal('12.34'),
    # when query takes place.
    if value is not None:
      value = Decimal(value) / self.multiplier_int
    return value

