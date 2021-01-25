from pyjuque.Engine.Models.BotModels import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from time import time


def get_session(path='sqlite:///'):
    some_engine = create_engine(path, echo=False)
    Base.metadata.create_all(some_engine)
    Session = sessionmaker(bind=some_engine)
    session = Session()
    return session


def timeit(function, text=None, *args):
	''' Used to print the time it takes to run a certain function. '''
	start = time()
	ret = function(*args)
	end = time()
	if text is not False:
		if text is None or text == "":
			text = function.__name__+" took "
		print(text+str(round(end - start, 4))+" s")
	return ret, end - start
