#!/usr/bin/python3
import subprocess
import os

currdir = os.path.relpath(os.path.dirname(__file__), start=os.getcwd())
sourcedir = os.path.normpath(os.path.join(currdir, '..', '..', 'cherrymusicserver'))

print('updating pot file')
subprocess.call('xgettext --language=Python --keyword=_ --add-comments=i18n --output='+currdir+'/cherrymusic.pot --from-code=UTF-8 `find '+sourcedir+' -name "*.py"`', shell=True)
print('updating all translations')
for translation in os.listdir(currdir):
    transfile = os.path.join(currdir, translation)
    if os.path.isdir(transfile):
        print('    merging %s' % transfile)
        subprocess.call('msgmerge --update '+transfile+'/LC_MESSAGES/default.po '+currdir+'/cherrymusic.pot', shell=True)
        print('    compiling %s' % transfile)
        subprocess.call('msgfmt -o '+transfile+'/LC_MESSAGES/default.mo -v '+transfile+'/LC_MESSAGES/default.po', shell=True)

