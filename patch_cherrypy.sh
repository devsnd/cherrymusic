#!/bin/sh

patch=$1
cherrypy=$(python -c "import os, cherrypy; print(os.path.split(cherrypy.__file__)[0])")
patch -p1 -d ${cherrypy} < ${patch}
