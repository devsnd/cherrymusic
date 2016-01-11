#!/bin/bash
coverage run --source='.' manage.py test cherrymusic.apps -v 2 && \
coverage report --skip-covered