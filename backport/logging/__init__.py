#!/usr/bin/python3
# -*- coding: utf-8 -*-

from logging import *
import sys
if sys.version_info < (2,7):
    StreamHandler.__realinit__ = StreamHandler.__init__
    def initStreamHandler(self,stream):
        StreamHandler.__realinit__(self)
    StreamHandler.__init__ = initStreamHandler
    
