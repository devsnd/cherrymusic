#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3,):
    from urllib2 import *
    from urllib import unquote
    from urlparse import urlparse
