# this assumes that the project is in a git repo
HASH = $(shell git rev-parse --short HEAD)
TAG = registry.mycoolsite.com:8000/may-$(HASH)

develop:
	docker-compose -f docker-compose.dev.yml up --build

build:
	docker build -t may .
	docker tag may $(TAG)
	docker push $(TAG)

tests_unit:
	npm run test

tests_integration:
	./integration_tests.sh

deploy_staging:
	cd deploy && ansible-playbook deploy.yml -e "stage=staging"

deploy_prod:
	cd deploy && ansible-playbook deploy.yml -e "stage=prod"
