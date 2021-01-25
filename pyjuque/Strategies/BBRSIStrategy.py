from pyjuque.Strategies.BaseStrategy import Strategy

class BBRSIStrategy(Strategy):
    """ Bollinger Bands x RSI Indicator
        Params
        --
            `rsi_len` = length of RSI
            `bb_len` = length of Bollinger Bands
            `rsi_ob` = Overbought level of RSI
            `rsi_os` = Oversold level of RSI
    """
    def __init__(self,
        rsi_len = 8,
        bb_len = 100,
        rsi_ob = 50,
        rsi_os = 50):
        self.rsi_ob = rsi_ob
        self.rsi_os = rsi_os
        self.bb_len = bb_len
        self.rsi_len = rsi_len
        self.minimum_period = max(100, bb_len, rsi_len)
        self.indicators = (
            dict(indicator_name = 'rsi', col_name = 'rsi', 
                source='close', period = self.rsi_len),
            dict(indicator_name = 'lbb', col_name = 'lbb', 
                source='close', period = self.bb_len),
            dict(indicator_name = 'ubb', col_name = 'ubb', 
                source='close', period = self.bb_len))


    def checkLongSignal(self, i):
        df = self.df
        
        if i < 3:
            return False

        if (df["rsi"][i] / df["rsi"][i-1] > 1.2) and \
            (df["rsi"][i-1] < self.rsi_os \
                or df["rsi"][i-2] < self.rsi_os \
                or df["rsi"][i-3] < self.rsi_os):
                
            if ((df["open"][i] < df["lbb"][i] < df["close"][i]) and \
                (df["open"][i-1] < df["lbb"][i-1] and df["close"][i-1] < df["lbb"][i-1])):
                return True

        if (df["rsi"][i-1] / df["rsi"][i-2] > 1.2) and \
            (df["rsi"][i-1] < self.rsi_os \
                or df["rsi"][i-2] < self.rsi_os \
                or df["rsi"][i-3] < self.rsi_os):
            if (df["close"][i-3] < df["lbb"][i-3] and df["close"][i-2] < df["lbb"][i-2] \
                and df["close"][i-1] > df["lbb"][i-1] and df["close"][i] > df["lbb"][i]):
                return True

        return False


    def checkShortSignal(self, i):
        df = self.df
        
        if i < 1:
            return False
        
        if (df["rsi"][i] < self.rsi_ob) and \
            (df["rsi"][i-1] >= self.rsi_ob) and \
            (df["close"][i] < df["ubb"][i] < df["open"][i]):
            return True
        return False
