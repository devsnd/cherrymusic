#!/bin/sh

patch="$1"

# if we're in a Travis CI environment
if [ $TRAVIS_PYTHON_VERSION ]; then
	pyversion=$TRAVIS_PYTHON_VERSION
	cherrypy="../../lib/python${pyversion}/site-packages/cherrypy"
fi

# we're probably not in Travis
if [ ! -d $cherrypy ]; then
	if [ $2 ]; then
		cherrypy="$2"
	else
		# try to get cherrypy location from within python
		cherrypy=$(python -c "import os, cherrypy; print(os.path.split(cherrypy.__file__)[0])")
	fi
fi

patch -p1 -d "$cherrypy" < "$patch"
