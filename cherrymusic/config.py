"""This class handles the configuration file loading,
it should be replaced by the python configuration/
config module"""

class Config(object):
    def __init__(self):
        self.BASEDIR = 'basedir'
        self.DOWNLOADABLE = 'downloadable'
        self.PLAYABLE = 'playable'
        self.HOSTALIAS = 'hostalias'
        self.MAXSHOWFOLDERS = 'maxshowfolders'
        self.CACHEENABLED = 'cacheenabled'
        self.CACHEFILE = 'cachefile'
        self.MAXSEARCHRESULTS = 'maxsearchresults'
        self.USER = 'user'
        self.SALT = 'salt'
        params = [
                self.BASEDIR,
                self.DOWNLOADABLE,
                self.PLAYABLE,
                self.MAXSHOWFOLDERS,
                self.CACHEENABLED,
                self.CACHEFILE,
                self.MAXSEARCHRESULTS,
                self.HOSTALIAS,
                self.USER,
                self.SALT                
                ]
        confpath = 'config'
        conflines = open(confpath).readlines()
        self.config = {}
        for line in conflines:
            #remove newline and so on.
            line = line.strip()
            for param in params:
                self.parseconfigparam(line,param)
        if not self.BASEDIR in self.config:
            raise Exception('Please specify the BASEDIR variable in your config file.')
        self.splitparams(self.DOWNLOADABLE, tupleize=True)
        self.splitparams(self.PLAYABLE, tupleize=True)
        self.config[self.MAXSHOWFOLDERS] = int(self.config[self.MAXSHOWFOLDERS])
        self.config[self.MAXSEARCHRESULTS] = int(self.config[self.MAXSEARCHRESULTS])
        self.config[self.CACHEENABLED] = bool(self.config[self.CACHEENABLED])
        
    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def parseconfigparam(self,line,param):
        #make sure each config param is not None
        if not param in self.config:
            self.config[param] = ''

        #set param if availbale
        if line.lower().startswith(param+'='):
            if param.lower() == self.USER.lower():
                #parse user credentials
                val = line[len(param+'='):].strip()

                if self.config[param] == '':
                    self.config[param] = {}
                pair = val.split(':')
                self.config[param][pair[0]] = pair[1]
                print('Added user '+pair[0])
            else:
                self.config[param] = line[len(param+'='):].strip()
                print(param+' set to '+self.config[param])

    def splitparams(self,param,tupleize=False,splitby=' ',isdict=False):
        if param in self.config:
            if isdict:
                pair = self.config[param].split(splitby)
                self.config[param][pair[0]] = pair[1]
            else:
                self.config[param] = self.config[param].split(splitby)
                if tupleize:
                    self.config[param] = tuple(self.config[param])

