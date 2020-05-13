import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
	os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

# Import all Created exchanges here
from bot.exchanges.Binance import Binance

# Basic Test
def test_exchange(exchange):
	response = exchange.getTradingSymbols()
	assert isinstance(response, list)
	
	exchange.addCredentials("invalid_api_key", "invalid_secret_key")
	assert exchange.has_credentials is True, \
		"Exchange should have credentials now."

	response = exchange.getAccountData()
	assert isinstance(response, dict)
	assert response.__contains__('code'), \
		"Response should contain an error since the api-secret key pair \
			is invalid."
	
	df = exchange.getSymbolKlines("BTCUSDT", '1m')
	for x in ['open', 'high', 'low', 'close', 'volume']:
  		assert x in df.columns, \
				x+" should be a column in the Candlestick dataframe."

def Main():
	# Initialize exchanges and test
	binance = Binance()
	test_exchange(binance)

	print("All tests passed fine.")

if __name__ == '__main__':
	Main()