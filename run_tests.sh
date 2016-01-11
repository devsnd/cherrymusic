#!/bin/bash
docker-compose build
docker-compose -f test.yml build
docker-compose -f test.yml up -d
docker-compose -f test.yml run --rm web_test /usr/src/test.sh && \
docker-compose -f test.yml stop