from distutils.core import setup
import os
import cherrymusicserver
import subprocess
import codecs
from cherrymusicserver import pathprovider
try:
    import py2exe
except ImportError:
    pass

import gzip
def gzipManPages():
    localManPagePath = 'doc/man'
    for manpage in os.listdir(localManPagePath):
        #man pages end in numbers
        if manpage.endswith(tuple(map(str,range(10)))):
            manpagefn = os.path.join(localManPagePath, manpage)
            with open(manpagefn, 'rb') as manfile:
                manfilegz = gzip.open(manpagefn+'.gz', 'wb')
                manfilegz.writelines(manfile)
                manfilegz.close()

def listFilesRec(crawlpath, installpath, filterfunc=None):
    filesperfolder = []
    for r,d,f in os.walk(crawlpath):
        files = []
        for name in f:
            if filterfunc:
                if not filterfunc(name):
                    continue
            files += [os.path.join(r,name)]
        filesperfolder += [(os.path.join(installpath,r),files)]
    return filesperfolder

def module(foldername):
    ret = [foldername]
    for i in os.listdir(foldername):
        if i == '__pycache__':
            continue
        subfolder = os.path.join(foldername, i)
        if os.path.isdir(subfolder) and _ispackage(subfolder):
            ret += module(subfolder)
            ret += [subfolder.replace(os.sep,'.')]
    return ret

def _ispackage(foldername):
    return '__init__.py' in os.listdir(foldername)

def packagedata(pkgfolder, childpath=''):
    ret = []
    for n in os.listdir(os.path.join(pkgfolder, childpath)):
        if n == '__pycache__':
            continue
        child = os.path.join(childpath, n)
        fullchild = os.path.join(pkgfolder, child)
        if os.path.isdir(fullchild):
            if not _ispackage(fullchild):
                ret += packagedata(pkgfolder, child)
        elif os.path.isfile(fullchild):
            if not os.path.splitext(n)[1].startswith('.py'):
                ret += [child]
    return ret

#setup preparations:
gzipManPages()
shareFolder = os.path.join('share',pathprovider.sharedFolderName)

# files to put in /usr/share
data_files = listFilesRec('res',shareFolder)

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
    package_data = {
        'cherrymusicserver.database.defs': packagedata('cherrymusicserver/database/defs'),
    },
    #startup script
    scripts = ['cherrymusic','cherrymusicd','cherrymusic-tray'],
    
    #py2exe specific
    console = [
        {
            "icon_resources": [(1, "res/favicon.ico")],
            "script":'cherrymusic'
        }
    ],
    data_files=data_files
)
