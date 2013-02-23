#!/bin/sh

patch="$1"

if [ "$2" ]; then
	cherrypy="$2"
else
	if [ $TRAVIS_PYTHON_VERSION ]; then
		echo "trying travis environment..."
		pyversion=$TRAVIS_PYTHON_VERSION
		cherrypy="../../lib/python${pyversion}/site-packages/cherrypy"
		if [ ! -d $cherrypy ]; then
			cherrypy="/home/travis/virtualenv/python${pyversion}/lib/python${pyversion}/site-packages/cherrypy"
		fi
	fi
fi

if [ ! $cherrypy ]; then
	echo "trying to get cherrypy location from within python"
	cherrypy=$(python -c "import os, cherrypy; print(os.path.split(cherrypy.__file__)[0])")
	if [ $? -ne 0 ]; then
		exit 1
	fi
fi

echo "using dir ${cherrypy}"
patch -p1 -d "$cherrypy" < "$patch"
