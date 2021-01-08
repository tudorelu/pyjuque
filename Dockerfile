FROM jackton1/alpine-python3-numpy-pandas:latest
RUN apk update
RUN apk add make automake gcc g++ kmod kbd
WORKDIR /usr/src/app
VOLUME ["./db"]
RUN python3 -m pip install yaspin
COPY docker_requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r docker_requirements.txt
COPY . .

# If you want the container to run the bot by running `docker run -it --name pyjuque pyjuque`
# CMD [ "python3", "./examples/try_BotController.py" ]




# 1. build
# docker build -t pyjuque .

# 2. run
# docker run -it --name pyjuque pyjuque python3 examples/try_BotController.py

# 3. kill (in other shell)
# docker kill $(docker ps -aq)

# nuke the container and then run 2. again
# docker container rm $(docker container ls -aq) 