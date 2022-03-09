from pandas import read_csv, to_datetime
from numpy import array

def load_data_from_file(filename:str='./data/BTCUSD_1m_1k.csv'):
    df = read_csv(filename)
    df = df.drop('Unnamed: 0', axis=1)
    df['DateTime'] = to_datetime(df['date'], infer_datetime_format=True)
    return df

def to_position_array(longs, shorts):
    long_signals = array(longs)
    short_signals = array(shorts)
    switch = long_signals - short_signals
    position_array = []
    current_position = 0
    for s_i in switch.tolist():
        if s_i != 0:
            current_position = s_i
        position_array.append(current_position)
    position_array = array(position_array)
    return position_array
