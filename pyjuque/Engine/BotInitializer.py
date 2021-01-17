import os
import yaml
import glob, importlib

def getStrategies():
    # Import all strategies by name from folder 
    Strategies = {}
    __globals = globals()
    for path in glob.glob('pyjuque/Strategies/[!_]*.py'):
        path, file = os.path.split(path)
        mod_name = file[:-3]
        if mod_name != 'BaseStrategy':
            mod_path = path.replace("/", ".") +'.' + mod_name
            Strategies[mod_name] = getattr(importlib.import_module(mod_path), mod_name)
    return Strategies

def getYamlConfig(bot_name = None):
    # Import bot templates 
    with open(r'bots_config.yml') as file:
        bots = yaml.load(file, Loader=yaml.FullLoader)['bots']
        if bot_name is not None:
            for bot_config in bots:
                if bot_config['name'] == bot_name:
                    return bot_config
        return bots[0]