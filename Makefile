.DELETE_ON_ERROR:
.SECONDARY:
.SECONDEXPANSION:

SHELL := /bin/bash -e -o pipefail

VIRTUALENV = source env/bin/activate &&
MANAGE = $(VIRTUALENV) python manage.py

.PHONY: env

help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  lint        check style with flake8"
	@echo "  server"
	@echo "  shell"
	@echo "  test        run all your tests using py.test"

env:
	virtualenv env
	$(VIRTUALENV) pip install -r requirements/dev.txt

server shell test:
	$(VIRTUALENV) python manage.py $@

lint:
	$(VIRTUALENV) flake8 --exclude=env .

docker-build:
	mv Dockerfile.local Dockerfile
	sudo docker build -t p13n-beanstalk-image .
	mv Dockerfile Dockerfile.local

docker-run:
	sudo docker run -it --rm -p 80:8080 p13n-beanstalk-image
