from distutils.core import setup
import os
import cherrymusicserver

try:
    import setuptools   # for python 3, this is provided by distribute: http://pypi.python.org/pypi/distribute
except ImportError:
    setuptools = None   # t'is ok, but `setup.py test` won't work

def listFilesRec(crawlpath, installpath):
    filesperfolder = []
    for r,d,f in os.walk(crawlpath):
        files = []
        for name in f:
            files += [os.path.join(r,name)]
        filesperfolder += [(os.path.join(installpath,r),files)]
    return filesperfolder

setup( 
    name = "CherryMusic",
    version = cherrymusicserver.VERSION,
    description="an mp3 server for your browser",
    long_description="""CherryMusic is a music streaming
    server based in cherrypy and jPlayer. You can search
    your collection, create and share playlists with
    other users.
    """,
    author = "Tom Wallroth & Tilman Boerner",
    author_email="tomwallroth@gmail.com, tilman.boerner@gmx.net",
    url = "http://www.fomori.org/cherrymusic/",
    license = 'GPL',
    install_requires=["CherryPy >= 3.2.2"],
    packages = ['cherrymusicserver','cherrymusicserver.test','audioread'],#,'audiotranscode'],
    #startup script
    scripts = ['cherrymusic'],
    #data required by the declared packages
    data_files=listFilesRec('res','share/cherrymusic')+listFilesRec('themes','share/cherrymusic')
)
    
