from bot.Strategies.BaseStrategy import Strategy # pylint: disable=E0401

class EMACrossover(Strategy):

    def __init__(self):
        # Minimum period needed for indicators to be calculated
        self.minimum_period = 100
        self.chooseIndicators()

    def chooseIndicators(self):
        self.indicators = dict(indicator_name  = 'sma', col_name = 'sma_fast', period = 5), dict(indicator_name = 'sma', col_name = 'sma_slow', period = 25)

    def checkLongSignal(self, i):
        df = self.df
        if i > 0 and df['sma_fast'][i] >= df['sma_slow'][i] \
            and df['sma_fast'][i-1] < df['sma_slow'][i-1]:
            return True
        return False

    def checkShortSignal(self, i):
        return False

    def checkToExitPosition(self, i):
        return True
