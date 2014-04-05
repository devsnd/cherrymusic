#!/usr/bin/python3
import subprocess
import os
import sys
import codecs
import time

usage = """
%s --major
    prepare a major release, e.g. 1.3.5 --> 2.3.5
%s --minor
    prepare a minor release, e.g. 1.3.5 --> 1.4.5
%s --path
    prepare a patch release, e.g. 1.3.5 --> 1.3.6
""" % (__file__,__file__,__file__,)

if (2 > len(sys.argv) == 1) or not sys.argv[1] in ['--major','--minor','--patch']:
    print(usage)
    sys.exit(1)
else:
    release_type = sys.argv[1][2:]  # = 'major' 'minor' or 'patch'

CM_MAIN_FOLDER = os.path.join(os.path.dirname(__file__), '..')
os.chdir(CM_MAIN_FOLDER)

output = subprocess.check_output(['python', '-c', 'import cherrymusicserver; print(cherrymusicserver.__version__)'])
rawcmversion = codecs.decode(output, 'UTF-8')
major, minor, patch = [int(v) for v in rawcmversion.split('.')]
version_now = (major, minor, patch)
if release_type == 'major':
    version_next = (major+1, 0, 0)
elif release_type == 'minor':
    version_next = (major, minor+1, 0)
elif release_type == 'patch':
    version_next = (major, minor, patch+1)

######## CHANGE INIT SCRIPT VERSION NUMBER #####
initscript = None
with open('cherrymusicserver/__init__.py', 'r', encoding='UTF-8') as fh:
    initscript = fh.read()
    version_line_tpl = '''VERSION = "%d.%d.%d"'''
    version_now_line = version_line_tpl % version_now
    version_next_line = version_line_tpl % version_next
    if initscript.find(version_now_line) == -1:
        print('''Cannot find version string in startup script! Looking for:

%s
''' % version_now_line)
        sys.exit(1)
    print('Changing version number in startup script. %s --> %s' %
          (version_now_line, version_next_line))
    initscript = initscript.replace(version_now_line, version_next_line)
with open('cherrymusicserver/__init__.py', 'w', encoding='UTF-8') as fh:
    fh.write(initscript)


######## UPDATE CHANGELOG #####
changelog_lines = None
t = time.gmtime()
with open('CHANGES', 'r', encoding='UTF-8') as fh:
    changelog_lines = fh.readlines()
with open('CHANGES', 'w', encoding='UTF-8') as fh:
    fh.write('Changelog\n---------\n\n')
    fh.write('%d.%d.%d ' % version_next)
    fh.write('(%d-%02d-%02d)\n' % (t.tm_year, t.tm_mon, t.tm_mday))
    fh.write(' - FEATURE: ... new feature here!\n')
    fh.write(' - FIXED:\n')
    fh.write(' - IMPROVEMENT:\n\n')
    fh.write(''.join(changelog_lines[3:]))  # leave out header
subprocess.call(['nano', 'CHANGES'])

####### PREPARE COMMIT AND REVIEW DIFF

subprocess.call(['git', 'add', 'CHANGES'])
subprocess.call(['git', 'add', 'cherrymusicserver/__init__.py'])
subprocess.call(['git', 'diff', '--staged'])
if input('Are you happy now? (y/n)') != 'y':
    print('''user unhappy. revert changes with
git checkout CHANGES
git checkout cherrymusicserver/__init__.py
''')
    sys.exit(1)

print('creating tagged commit...')
version_name = 'release %d.%d.%d' % version_next
tag_name = '%d.%d.%d' % version_next
subprocess.call(['git', 'commit', '-m', '"%s"' % version_name])
subprocess.call(['git', 'tag', '-a', '-m', '"%s"' % version_name, tag_name])
print('''all done, you can push the changes now! e.g.:

git push --tags
''')

