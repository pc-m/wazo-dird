.PHONY: test-setup build-dird build-db-image egg-info test

test-setup: egg-info build-dird build-db-image
	docker pull alpine
	docker pull nickstenning/slapd
	docker pull p0bailey/docker-flask
	docker pull python:2.7.13-stretch
	docker pull rabbitmq
	docker pull swaggerapi/swagger-validator
	docker pull wazopbx/wait
	docker pull wazopbx/wazo-auth-mock

build-dird:
	docker build -t wazopbx/wazo-dird ..
	docker build --no-cache -t wazo-dird-test -f docker/Dockerfile-dird-test ..

build-db-image:
	docker build -f ../contribs/docker/Dockerfile-db -t wazopbx/wazo-dird-db ..

egg-info:
	cd .. && python setup.py egg_info
	cd docker/broken-plugins && python setup.py egg_info

test:
	pytest
