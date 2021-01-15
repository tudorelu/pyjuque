class BaseExchange:
    """
        Is the base class from which all Exchanges should inherit.
        Exchanges should implement all the functions outlined here (at least).

        As we add more exchanges to the bot & see different API implementations, 
        we will also update this class - so that it has the most elastic & modular 
        form, in case we observe that more functions are needed or that some need 
        to be updated.
    """

    def _get(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Calls a get request to this exchange """
        raise NotImplementedError

    def _post(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Calls a post request to this exchange """
        raise NotImplementedError

    def _delete(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Calls a delete request to this exchange """
        raise NotImplementedError

    def _signRequest(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Signs a request with the API & SECRET keys """
        raise NotImplementedError

    def addCredentials(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Adds API & SECRET keys into the object's memory """
        raise NotImplementedError

    def getAccountData(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Gets data for Account connected to API & SECRET Keys given """
        raise NotImplementedError
    
    def getTradingSymbols(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Gets All symbols which are tradable (currently) """
        raise NotImplementedError

    def getOrderBook(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Gets Order Book data for symbol """
        raise NotImplementedError

    def getOHLCV(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Gets Candlestick Book data for symbol on interval (IE 1 minute) """
        raise NotImplementedError

    def placeOrder(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Places order on exchange given a dictionary of parameters """
        raise NotImplementedError

    def placeMarketOrder(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Places side (buy/sell) market order for amount of symbol  """
        raise NotImplementedError

    def placeLimitOrder(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Places side (buy/sell) limit order for amount of symbol at price """
        raise NotImplementedError

    def cancelOrder(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Cancels order given order id """
        raise NotImplementedError

    def getOrder(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Gets order info given order id """
        raise NotImplementedError

    def isValidResponse(self, *args, **kwargs):
        """ (NOT IMPLEMENTED) 
        Checks whether response received from exchange is valid

        Returns 
        --
            True if valid, False otherwise
        """
        raise NotImplementedError
    