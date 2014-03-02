"""
This script is used to download cherrymusic dependencies on first startup.
"""

try:
    import urllib.request
except ImportError:
    from backport import urllib
from backport import input
import tempfile
import tarfile
import shutil
import os

class DependencyInstaller:
    def __init__(self):
        self.cherrymusicfolder = os.path.dirname(os.path.dirname(__file__))
        
    def install_cherrypy(self):
        """
        cherrypy releases: https://bitbucket.org/cherrypy/cherrypy/downloads
        """
        cherrypygitcommit = "586bee7ac445"
        cherrypyurl = "https://bitbucket.org/cherrypy/cherrypy/get/%s.tar.gz" % cherrypygitcommit
        cherrypysubfolder = os.path.join('cherrypy-cherrypy-%s'%cherrypygitcommit,'cherrypy')
        cherrypytempfile = os.path.join(tempfile.gettempdir(),'cherrypy.tar.gz')
        cherrypytempdir =  self.tmpdir('cherrypy')
        print('Downloading cherrypy...')
        self.dl(cherrypyurl, cherrypytempfile)
        print('Extracting %s ' % cherrypytempfile)
        tarc = tarfile.open(cherrypytempfile,'r:gz')
        tarc.extractall(cherrypytempdir)
        tarc.close()
        print('Copying cherrypy module inside cherrymusic folder (%s)...' % self.cherrymusicfolder)
        moduledir = os.path.join(cherrypytempdir,cherrypysubfolder)
        shutil.copytree(moduledir,os.path.join(self.cherrymusicfolder,'cherrypy'))
        print('Cleaning up temporary files...')
        shutil.rmtree(cherrypytempdir)
        os.remove(cherrypytempfile)      
    
    def tmpdir(self, name):
        tempdirpath = os.path.join(tempfile.gettempdir(),name)
        if os.path.exists(tempdirpath):
            print("Directory %s already exists." % tempdirpath)
            if 'y' == input('Do you want to delete its contents and proceed? [y/n]'):
                shutil.rmtree(tempdirpath)
            else:
                print("Cannot install dependency.")
                exit(1)
        os.mkdir(tempdirpath)
        return tempdirpath
    
    def dl(self,url,target):
         with open(target, 'wb') as f:
            urlhandler = urllib.request.urlopen(urllib.request.Request(url))
            f.write(urlhandler.read())
        
import sys
try:
    import cherrypy
except ImportError:
    print('''
    CherryMusic needs the module "cherrypy" to run. You should install it 
    using the package manager of your OS. Alternatively cherrymusic can 
    download it for you and put it in the folder in which currently
    CherryMusic resides.
    ''')
    if input("Download cherrypy now? (y/n)") == 'y':
        inst = DependencyInstaller()
        inst.install_cherrypy()
        print('Successfully installed cherrymusic dependencies! You can now start cherrymusic.')
    else:
        sys.exit(1)
