build:
		docker build -t weather --build-arg environment=dev .

start:
		docker run -itd weather
		docker exec -it `docker ps -lq` bash

stop:
		docker container rm -f `docker ps -lq`

tests:
		docker build -t weather-test --build-arg environment=test .
		docker run weather-test
