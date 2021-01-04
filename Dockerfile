# FROM python:3.6-alpine
FROM jackton1/alpine-python3-numpy-pandas:latest
# FROM tailordev/pandas
RUN apk update
RUN apk add make automake gcc g++ kmod kbd
# RUN apk add make automake gcc g++ subversion python3-dev libffi-dev musl-dev
WORKDIR /usr/src/app
VOLUME ["./db"]
RUN python3 -m pip install yaspin keyboard
# RUN ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future python3 -m pip install --upgrade numpy
COPY docker_requirements.txt ./
# RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r docker_requirements.txt
COPY . .
# CMD [ "python3", "./examples/try_BotController.py" ]

# reset
# docker container rm $(docker container ls -aq) 

# build
# docker build -t pyjuque .

# run
# docker run -it --name pyjuque pyjuque python3 examples/try_BotController.py

# kill
# docker kill $(docker ps -aq)