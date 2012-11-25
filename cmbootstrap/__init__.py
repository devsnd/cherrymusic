import urllib.request
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
    
    def install_stagger(self):
        staggerfiles = [
            "http://stagger.googlecode.com/svn/trunk/stagger/__init__.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/commandline.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/conversion.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/errors.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/fileutil.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/frames.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/id3.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/id3v1.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/specs.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/tags.py",
            "http://stagger.googlecode.com/svn/trunk/stagger/util.py"
        ]
        print('Downloading stagger...')
        staggerfolder = os.path.join(self.cherrymusicfolder,'stagger')
        os.mkdir(staggerfolder)
        for sta in staggerfiles:
            filename = os.path.join(staggerfolder, sta[sta.rindex('/')+1:])
            print('   '+filename)
            self.dl(sta, filename)
        print('done')
    
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
        
