try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os
import cherrymusicserver
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

setup_options = {
    'name': "CherryMusic",
    'version': cherrymusicserver.VERSION,
    'description': cherrymusicserver.DESCRIPTION,
    'long_description': cherrymusicserver.LONG_DESCRIPTION,
    'author': "Tom Wallroth & Tilman Boerner",
    'author_email': "tomwallroth@gmail.com, tilman.boerner@gmx.net",
    'url': "http://www.fomori.org/cherrymusic/",
    'license': 'GPLv3',
    'install_requires': ["CherryPy >= 3.2.2"],
    'packages': module('cherrymusicserver')+module('audioread')+module('audiotranscode')+module('cmbootstrap')+module('backport'),
    'package_data': {
        'cherrymusicserver.database.defs': packagedata('cherrymusicserver/database/defs'),
    },
    #startup script
    'scripts': ['cherrymusic','cherrymusicd','cherrymusic-tray'],
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: CherryPy",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        ],
    'data_files': data_files
}

if os.name == 'nt':
    #py2exe specific
    setup_options['console'] = [
        {
            "icon_resources": [(1, "res/favicon.ico")],
            "script":'cherrymusic'
        }
    ]

setup(**setup_options)
