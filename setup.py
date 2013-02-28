from distutils.core import setup
import os
import cherrymusicserver
from cherrymusicserver import pathprovider
try:
    import py2exe
except ImportError:
    pass

def listFilesRec(crawlpath, installpath):
    filesperfolder = []
    for r,d,f in os.walk(crawlpath):
        files = []
        for name in f:
            files += [os.path.join(r,name)]
        filesperfolder += [(os.path.join(installpath,r),files)]
    return filesperfolder

def module(foldername):
    ret = [foldername]
    for i in os.listdir(foldername):
        if i == '__pycache__':
            continue
        subfolder = os.path.join(foldername, i)
        if os.path.isdir(subfolder):
            ret += module(subfolder)
            ret += [subfolder.replace(os.sep,'.')]
    return ret

shareFolder = os.path.join('share',pathprovider.sharedFolderName)
                
setup( 
    name = "CherryMusic",
    version = cherrymusicserver.VERSION,
    description=cherrymusicserver.DESCRIPTION,
    long_description=cherrymusicserver.LONG_DESCRIPTION,
    author = "Tom Wallroth & Tilman Boerner",
    author_email="tomwallroth@gmail.com, tilman.boerner@gmx.net",
    url = "http://www.fomori.org/cherrymusic/",
    license = 'GPL',
    install_requires=["CherryPy >= 3.2.2"],
    packages = module('cherrymusicserver')+module('audioread')+module('audiotranscode')+module('cmbootstrap')+module('backport'),
    #startup script
    scripts = ['cherrymusic','cherrymusicd'],
    console = [
        {
            "icon_resources": [(1, "res/favicon.ico")],
            "script":'cherrymusic'
        }
    ],
    #data required by the declared packages
    data_files=listFilesRec('res',shareFolder)
)
    
