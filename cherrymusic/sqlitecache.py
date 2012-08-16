import os
from time import time
import sqlite3
from io import StringIO
from operator import itemgetter
import re

CACHEFILENAME = 'cherry.cache.db' #set to ':memory:' to keep _everything_ in ram
scanreportinterval = 1
AUTOSAVEINTERVAL = 50
debug = False
performanceTest = False
keepInRam = False

from cherrymusic import config

class SQLiteCache(object):
    def __init__(self, conf):
        DBFILENAME = CACHEFILENAME
        setupDB = not os.path.isfile(DBFILENAME) or os.path.getsize(DBFILENAME) == 0
        setupDB |= DBFILENAME == ':memory:' #always rescan when using ram db.
        print('Starting database... ')
        
        self.conn = sqlite3.connect(DBFILENAME, check_same_thread = False)
        self.db = self.conn.cursor()
        self.rootDir = conf.config[conf.BASEDIR] 
        
        if setupDB:
            print('Creating tables...')
            # Create table
            self.db.execute('CREATE TABLE files (parent int, filename text, filetype text, isdir int)')
            self.db.execute('CREATE TABLE dictionary (word text)')
            self.db.execute('CREATE TABLE search (drowid int, frowid int)')
            print('Creating index for dictionary and search tables... ',end='')
            self.conn.execute('CREATE INDEX idx_dictionary ON dictionary(word)')
            self.conn.execute('CREATE INDEX idx_search ON search(drowid,frowid)');
            print('done.')
            print('Connected to Database. ('+DBFILENAME+')')
        #I don't care about journaling!
        self.conn.execute('PRAGMA synchronous = OFF')
        self.conn.execute('PRAGMA journal_mode = MEMORY')
        self.checkIfRootUpdated()                       
    
    def checkIfRootUpdated(self):
        changed = False
        print('Checking if root folder is up to date...')
        self.db.execute('''SELECT rowid, filename, filetype FROM files WHERE parent = -1''')
        dbrootfilelist = self.db.fetchall()
        dbrootfiledict = {}
        for id, filename, ext in dbrootfilelist:
            dbrootfiledict[id] = filename+ext
        dbrootfilelist = [] #free mem
        print('{} folders in db root'.format(len(dbrootfiledict)))
        realrootfiles = os.listdir(self.rootDir)
        print('{} folders in fs root'.format(len(realrootfiles)))
        print('Comparing db with filesystem...')
        
        removeList = [] #list of db ids
        addList = [] #list of file system paths
        
        for dbrootfile in dbrootfiledict.items():
            if not dbrootfile[1] in realrootfiles:
                removeList.append(dbrootfile[0])
                
        for realfile in realrootfiles:
            if realfile not in dbrootfiledict.values():
                addList.append(realfile)

        #addList = sorted(addList)
        #removeList = sorted(removeList)
        if len(removeList)>0 or len(addList)>0:
            if 'y' == input("Changes detected ({} added, {} removed), perform rescan? (y/n)".format(len(addList),len(removeList))):
                starttime = time()
                added = 0
                for addItem in addList:
                    print(str(len(addList)-added).rjust(4)+'/'+str(len(addList))+' ',end='')
                    print('adding '+addItem.ljust(30,' ')+'ETA: '+self.eta(starttime,added/len(addList)))
                    self.scan((self.rootDir,addItem), -1)
                    added +=1
                    self.autosave(added)
                    changed = True
                    
                removed = 0
                starttime = time()
                for removeItem in removeList:
                    print('removing file with id: '+str(removeItem) +' ...'+self.eta(starttime,removed/len(removeList)))
                    self.removeFromDB(removeItem)
                    self.autosave(removed)
                    changed = True
                    removed += 1
                
        if changed:
            print('Commiting changes...', end='')
            self.conn.commit()
            print('done.')        
                
    def removeFromDB(self,filerowid):
        print("""removeFromDB: NOT IMPLEMENTED! should remove file """+str(filerowid))
            
    def addToDB(self, parentid, pathtofile, filename, isdir):
        filename, ext = SQLiteCache.splitext(filename)
        try:
            self.db.execute('INSERT INTO files VALUES (?,?,?,?)', (parentid, filename, ext, 1 if isdir else 0) )
        except UnicodeEncodeError:
            print("WRONG ENCODING OF FILENAME! exiting...")
            print(pathtofile, filename, ext)
            print('Saving current status...', end='')
            self.conn.commit()
            print('done.')
            exit(1)
        return self.db.lastrowid

    def scan(self, dir, parentid, toplevel=False):
        #if given a tuple, it will scan and add all folders in that tuple (rootpath, dirtoscan) 
        if type(dir) == tuple:
            dirlist = [dir[1]]
            dir = dir[0]
        else:
            #otherwise it adds all folders within a path
            dirlist = sorted(os.listdir(dir))
        
        if toplevel:
            scannedfolders = 0
            foldercount = len(dirlist)
            print(str(foldercount)+' folders in root directory')
            starttime = time()
            actualstarttime = time()
            
        for entry in dirlist:
            fullpath = os.path.join(dir, entry)
            isdir = os.path.isdir(fullpath)
            subparentid = self.addToDB(parentid, dir, entry, isdir)
            if subparentid < -1: #error
                continue
            self.addToDictionary(subparentid, entry)
            if(isdir):
                self.scan(fullpath,subparentid)
            
            if toplevel:
                self.autosave(scannedfolders)
                if time() > starttime + scanreportinterval:
                    print('{} / {} scanned root folders ({}% - ETA {}s)'.format(
                            scannedfolders,
                            foldercount,
                            int(scannedfolders/foldercount*1000)/10,
                            self.eta(actualstarttime,(scannedfolders+1)/foldercount)))
                            
                    starttime = time()
                scannedfolders += 1
        if toplevel:
            print('Scan finished!')
    
    def eta(self,start,percent):
        if percent <= 0:
            return 'n/a'
        remainings = (time()-start)/percent
        sec = int(remainings)
        min = int(sec/60)
        sec = sec%60
        hr = int(min/60)
        min = min%60
        return '{}h {}m {}s '.format(hr,min,sec)
    
    def autosave(self, count):
        if count % AUTOSAVEINTERVAL == 0:
            print('===> Autosaving ... ',end='')
            self.conn.commit()
            print('done <===')
    
    def addToDictionary(self, filerowid, filename):
        for word in SQLiteCache.searchterms(filename):
            self.db.execute('''SELECT rowid FROM dictionary WHERE word = ? LIMIT 0,1''',(word,))
            wordrowid = self.db.fetchone()
            if wordrowid == None:
                self.db.execute('''INSERT INTO dictionary VALUES (?)''', (word,))
                wordrowid = self.db.lastrowid
            else:
                wordrowid = wordrowid[0]
            self.db.execute('INSERT INTO search VALUES (?,?)', (wordrowid,filerowid))
            
    def searchterms(searchterm):
        words = re.findall('(\w+)',searchterm.replace('_',' '))
        return list(map(lambda x:x.lower(),words))

    def splitext(filename):
        if '.' in filename:
            dotindex = filename.rindex('.')
            return (filename[:dotindex], filename[dotindex:])
        return (filename,'')
    
    def fetchFileIds(self,terms):
        resultlist = []
        for term in terms:
            query = '''SELECT search.frowid FROM dictionary JOIN search ON search.drowid = dictionary.rowid WHERE dictionary.word = ?'''
            limit = ' LIMIT 0, 250' #TODO add maximum db results as configuration parameter
            print('Search term: '+term)
            sql = query+limit
            if performanceTest:
                print('Query used: '+sql)
            self.db.execute(sql,(term,));
            resultlist += self.db.fetchall()
        
        return resultlist
    
    def searchfor(self,value,maxresults=10):
        starttime = time()
        self.db = self.conn.cursor()
        terms = SQLiteCache.searchterms(value)
        if debug:
            print('searchterms')
            print(terms)
        results = []
        resultfileids = {}

        print('querying terms: '+str(terms))
        perf()
        fileids = self.fetchFileIds(terms)
        perf('file id fetching')
            
        if debug:
            print('fileids')
            print(fileids)
        for fileid in fileids:
            if fileid in resultfileids:
                resultfileids[fileid] += 1
            else:
                resultfileids[fileid] = 1
                
        if debug:
            print('all file ids')
            print(resultfileids)
        #sort items by occurences and only return maxresults
        sortedresults = sorted(resultfileids.items(), key=itemgetter(1), reverse=True)
        #sortedresults = sortedresults[:min(len(resultfileids),maxresults)]
        if debug:
            print('sortedresults')
            print(sortedresults)
        bestresults = list(map(itemgetter(0),sortedresults))
        if debug:
            print('bestresults')
            print(bestresults)
        perf()
        for fileidtuple in bestresults:
            results.append(self.fullpath(fileidtuple[0]))
        perf('querying fullpaths')
        if debug:
            print('resulting paths')
            print(results)
        if performanceTest:
            print('overall search took '+str(time()-starttime)+'s')
        return results
                    
    def fullpath(self,filerowid):
        path = ''
        parent = None
        while(not parent == -1):
            cursor = self.conn.cursor()
            cursor.execute('''SELECT parent, filename, filetype FROM files WHERE rowid=? LIMIT 0,1''',(filerowid,))
            parent, filename, fileext = cursor.fetchone()
            path = os.path.join(filename+fileext,path)
            filerowid = parent
        return os.path.dirname(path)
        
def perf(text=None):
        global __perftime
        if text == None:
            __perftime = time()
        else:
            print(text+' took '+str(time()-__perftime)+'s to execute')