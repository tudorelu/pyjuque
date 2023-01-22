install:
	pip install --upgrade pip && pip install -r requirements.txt

install-dev:
	pip install -r requirements_dev.txt

lint:
	pylint --disable=R,C,W0511 ./pyjuque

test:
	coverage run --source=./pyjuque -m pytest && \
	coverage report

build:
	pytest && \
	python -m setup sdist
