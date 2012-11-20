import re
import os
import tempfile

class TranscodeCache:
    def __init__(self, maxTmpDirSizeMB = 50):
        self.maxTmpDirSizeBytes = maxTmpDirSizeMB*1024*1024
        self.tempdir = os.path.join(tempfile.gettempdir(),'.cherrymusic-cache')
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.cacheFiles = [CacheFile(os.path.join(self.tempdir,f)) for f in os.listdir(self.tempdir)]
    
    def getTmpFilePath(self,filepath,newformat):
        return os.path.join(self.tempdir,self.pathToFileName(filepath,newformat))
    
    def exists(self,filepath,newformat):
        exists = os.path.exists(self.getTmpFilePath(filepath,newformat)) 
        return exists and os.path.getsize(self.getTmpFilePath(filepath,newformat))>0
        
    def createCacheFile(self,filepath,newformat):
        self.checkQuotaAndDeleteOldest()
        tmpfile = self.getTmpFilePath(filepath,newformat)
        self.cacheFiles.append(CacheFile(tmpfile))
        return tmpfile
    
    def pathToFileName(self,filepath,newformat):
        return filepath.replace(os.sep,'_')+'.'+newformat
        
    def checkQuotaAndDeleteOldest(self):
        while(sum(map(lambda x:x.size, self.cacheFiles)) > self.maxTmpDirSizeBytes):
            self.cacheFiles = sorted(self.cacheFiles,key=lambda x:x.ctime)
            self.cacheFiles[0].delete()
            self.cacheFiles = self.cacheFiles[1:]
        for c in self.cacheFiles:
            c.update()
        
class CacheFile:
    def __init__(self, absfilepath):
        self.absfilepath = absfilepath
        self.update()
    
    def delete(self):
        os.remove(self.absfilepath)
               
    def update(self):
        try:
            self.ctime = os.path.getctime(self.absfilepath)
            self.size = os.path.getsize(self.absfilepath)
        except OSError:
            self.ctime = 0
            self.size = 0
        

