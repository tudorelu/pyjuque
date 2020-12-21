import numpy as np
from sklearn.decomposition import PCA
import pandas as pd
import pandas_ta as ta 
from pyjuque.Exchanges.Binance import Binance

exchange = Binance()
df = exchange.getSymbolKlines(symbol="BTCUSDT", interval="1h", limit=5100)
len(df)
df_original = df[['time', 'open', 'high', 'low', 'close', 'volume']]
df.ta.strategy()
len(df)

df = df.drop(columns=["time", "date"])
df = df.drop(df.index[:100])
df = df.dropna(axis = 1, how = 'any')

Y = df['EMA_10'].shift(-10) - df['EMA_10']
Y = Y.drop(Y.index[-10:])

################## ##################
df_size = len(df)
df_train = df[:int(df_size * 0.75)]
df_test = df[len(df_train):]

y_train, y_test = Y[:len(df_train)], Y[len(df_train):]
################## ##################

df_train = (df_train-df_train.mean())/df_train.std()
df_train.replace([np.inf, -np.inf], np.nan, inplace=True)
df_train = df_train.dropna(axis = 1, how = 'any')
len(df_train)

pca = PCA(n_components = 25)
pca.fit(df_train, y_train)

# variance = pca.explained_variance_ratio_ 
# var = np.cumsum(np.round(pca.explained_variance_ratio_, decimals = 3) * 100)
# var

columns = ['pca_%i' % i for i in range(25)]
df_pca = pd.DataFrame(pca.transform(df_train), columns=columns, index=df_train.index)
X_train = df_pca


df_test = (df_test-df_test.mean())/df_test.std()
df_test.replace([np.inf, -np.inf], np.nan, inplace=True)
df_test = df_test.dropna(axis = 1, how = 'any')
df_test = df_test.drop(df_test.index[-10:])
len(df_test)

df_pca = pd.DataFrame(pca.transform(df_test), columns=columns, index=df_test.index)
X_test = df_pca

from sklearn import preprocessing, svm 
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression 

# X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.25) 

regr = LinearRegression() 
regr.fit(X_train, y_train) 
print(regr.score(X_test, y_test)) 