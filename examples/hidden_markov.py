import os
import sys
curr_path = os.path.abspath(__file__)
root_path = os.path.abspath(
    os.path.join(curr_path, os.path.pardir, os.path.pardir))
sys.path.append(root_path)

import pandas as pd
import pandas_ta as TA
import numpy as np
from sklearn import mixture as mix

from pyjuque.Exchanges.Binance import Binance
from pprint import pprint
from pyjuque.Plotting.Plotter import PlotData

import plotly.graph_objs as go

class GaussianMixture():
  def __init__(self, candles):
    self.df = candles

  def get_regimes(self):
    df = self.df

    try:
      df = df.drop(columns = ['regime'], axis = 1)
    except:
      pass

    df['RSI'] = TA.rsi(df['close'], length = 14)
    df['ROC'] = TA.roc(df['close'], length = 14)

    df = df.dropna()

    means = np.array([
            [0, -10],
            [50, 0],
            [100, 10]
            ])
    

    df2 = df[['RSI','ROC']]

    unsup = mix.GaussianMixture(n_components=3, 
                            covariance_type="spherical", 
                            n_init=50,
                            means_init = means, 
                            random_state=42,
                        )
    
    unsup.fit(df2)
    regime = unsup.predict(df2)
    Regimes=pd.DataFrame(regime,columns=['regime'],index=df.index)
    con = [df, Regimes]
    # print(df, Regimes)
    return pd.concat(con, axis=1)


if __name__ == '__main__':
    exchange = Binance()
    df = exchange.getSymbolKlines('BTCUSDT', '1h', 3000)
    mixture = GaussianMixture(df)
    regimes = mixture.get_regimes()

    PlotData(regimes, add_candles=True,
      plot_title="fib_levels", show_plot=True, regimes_number=3)

    pprint(regimes)
    

