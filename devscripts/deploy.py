#!/usr/bin/python3

import subprocess as sp
import re
import os
import hashlib

MAIN_CM_FOLDER = os.path.dirname(os.path.dirname(__file__))

DEVEL_INPUT_HTML = os.path.join(MAIN_CM_FOLDER, 'res/devel.html')
MAIN_OUTPUT_HTML = os.path.join(MAIN_CM_FOLDER, 'res/dist/main.html')

LESSC = 'lessc'
JSMIN = 'jsmin'

def prog_exists(exe):
    try:
        with open(os.devnull,'w') as devnull:
            prog = sp.Popen([exe], stdin=devnull, stdout=devnull)
            stout, sterr = prog.communicate('')
    except IOError:
        print('Warning: "%s" was not found.' % exe)
        return False
    return True
    
if not (prog_exists(LESSC) and prog_exists(JSMIN)):
    print('''=== WARNING: CANNOT DEPLOY ===
For automatic deployment, please install jsmin and the less-css compiler
and make sure they are in your $PATH.''')
    exit(0)

def compile_less(in_less_file, out_css_file):
    LESSC_OPTS = ['--include-path='+os.path.dirname(in_less_file),'-'] #['--yui-compress', '-']
    print(" compiling %s to %s"%(in_less_file, out_css_file))
    with open(in_less_file, 'rb') as fr:
        with open(out_css_file, 'wb') as fw:
            less_file_dir = os.path.dirname(in_less_file)
            compiler = sp.Popen([LESSC]+LESSC_OPTS,
                                stdin=sp.PIPE,
                                stdout=sp.PIPE)
            stout, sterr = compiler.communicate(fr.read())
            fw.write(stout)
            print(" Wrote %s bytes."% fw.tell())

def parse_args(argsstr):
    argpairs = [x.split('=') for x in argsstr.strip().split(' ')]
    return dict(argpairs)

def match_less_compile(match):
    args = parse_args(match.group(1))
    lessfile = re.findall('href="([^"]+)', match.group(2))[0]
    outfile = args['out']
    compile_less(lessfile, outfile)
    return '<link href="%s" media="all" rel="stylesheet" type="text/css" />' % outfile

def compile_jsmin(instr, outfile):
     with open(outfile, 'wb') as fw:
        compiler = sp.Popen([JSMIN], stdin=sp.PIPE, stdout=sp.PIPE)
        stout, sterr = compiler.communicate(instr)
        fw.write(stout)
        print("compressed to %s bytes."% fw.tell())
        print("that's %d%% less" % (100 - fw.tell()/len(instr)*100) )

def match_js_concat_min(match):
    args = parse_args(match.group(1))
    jsstr = b''
    for scriptpath in re.findall('<script.*src="([^"]+)"', match.group(2)):
        with open(scriptpath, 'rb') as script:
            jsstr += script.read()
            jsstr += b';\n'
    jshash = hashlib.md5(jsstr).hexdigest()
    print('calculated hash %s' % jshash)
    print('js scripts uncompressed %d bytes' % len(jsstr))
    outfilename = args['out']
    #dotpos = outfilename.rindex('.')
    #outfilename = outfilename[:dotpos]+jshash+outfilename[dotpos:]
    compile_jsmin(jsstr, outfilename)
    return '<script type="text/javascript" src="%s"></script>' % outfilename

def remove_whitespace(html):
    no_white = re.sub('\s+', ' ', html, flags=re.MULTILINE)
    print('removed whitespace. before %d bytes, after %d bytes.' % (len(html), len(no_white)))
    print("that's %d%% less" % (100 - len(no_white)/len(html)*100) )
    return no_white

html = None
with open(DEVEL_INPUT_HTML, 'r') as develhtml:
    html = develhtml.read()

html = re.sub('<!--LESS-TO-CSS-BEGIN([^>]*)-->(.*)<!--LESS-TO-CSS-END-->',
              match_less_compile,
              html,
              flags=re.MULTILINE | re.DOTALL)
html = re.sub('<!--REMOVE-BEGIN-->(.*)<!--REMOVE-END-->',
              '',
              html,
              flags=re.MULTILINE | re.DOTALL)
html = re.sub('<!--COMPRESS-JS-BEGIN([^>]*)-->(.*)<!--COMPRESS-JS-END-->',
              match_js_concat_min,
              html,
              flags=re.MULTILINE | re.DOTALL)
html = remove_whitespace(html)

with open(MAIN_OUTPUT_HTML, 'w') as mainhtml:
    mainhtml.write(html)
