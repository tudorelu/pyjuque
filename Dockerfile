# FROM python:3.6-alpine
FROM jackton1/alpine-python3-numpy-pandas:latest
# FROM tailordev/pandas
RUN apk update
RUN apk add make automake gcc g++
# RUN apk add make automake gcc g++ subversion python3-dev libffi-dev musl-dev
WORKDIR /usr/src/app
VOLUME ["./db"]
RUN python3 -m pip install yaspin
# RUN ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future python3 -m pip install --upgrade numpy
COPY docker_requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r docker_requirements.txt
COPY . .
RUN ls -la
CMD [ "python3", "./examples/try_BotController.py" ]