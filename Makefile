SHELL := /bin/bash

all: generate_api

generate_api:
	bash -c "python ./cherrymusic/manage.py generate_swagger -f yaml > cherrymusic/api/generator/schema.yaml"
	bash -c "python ./cherrymusic/manage.py generate_typescript_api cherrymusic/api/generator/schema.yaml ./client/src/api/api.ts"
