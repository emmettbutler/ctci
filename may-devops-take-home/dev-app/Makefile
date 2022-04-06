# this assumes that the project is in a git repo
HASH = $(shell git rev-parse --short HEAD)
TAG = registry.mycoolsite.com:8000/may-$(HASH)

develop:
	docker-compose -f docker-compose.dev.yml up --build

build:
	docker build -t may .
	docker tag may $(TAG)
	docker push $(TAG)

tests:
	npm run test
