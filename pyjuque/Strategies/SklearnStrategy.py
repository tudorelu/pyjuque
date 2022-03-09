from pyjuque.Strategies import Strategy
# from pandas import DataFrame


class SklearnStrategy(Strategy):
    def __init__(self, model, features:str, target:str, 
                *model_args:list, **model_kwargs:dict):
        super().__init__()
        self.model = model(*model_args, **model_kwargs)
        self.features = features
        self.target = target


    # def set_up(self, candles:DataFrame):
    #     pass