build:
		docker build -t weather .

start:
		docker run -itd weather
		docker exec -it `docker ps -lq` bash

stop:
		docker container rm -f `docker ps -lq`
