#!/bin/bash
coverage run --source='./cherrymusic/apps' manage.py test cherrymusic.apps -v 2 && \
coverage report --skip-covered