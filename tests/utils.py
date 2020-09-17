
from time import time

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
