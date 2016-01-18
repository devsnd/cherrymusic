#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P)"
REPO_PATH="$( dirname $DIR)"

cd $REPO_PATH

docker-compose build web
docker-compose -f test.yml build
docker-compose -f test.yml up -d
docker-compose -f test.yml run --rm web_test /usr/src/test.sh && \
docker-compose -f test.yml stop