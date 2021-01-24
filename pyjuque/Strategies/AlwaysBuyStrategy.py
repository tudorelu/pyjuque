from pyjuque.Strategies.BaseStrategy import Strategy

class AlwaysBuyStrategy(Strategy):
    """ Always Buy Strategy:
    Buys when low < close and sells when close > low
    """
    minimum_period = 10
    indicators = None

    def checkLongSignal(self, i):
        return True

    def checkShortSignal(self, i):
        return False