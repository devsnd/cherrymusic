#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3,0):
    from . import urllib
    input = raw_input
else:
    input = input

if sys.version_info < (3,2):
    import optparse as argparse
    argparse.ArgumentParser = argparse.OptionParser
    argparse.ArgumentParser.add_argument = argparse.ArgumentParser.add_option
    argparse.ArgumentParser.__parse_args__ = argparse.ArgumentParser.parse_args
    def parseargs(self):
        return self.__parse_args__()[0]
    argparse.ArgumentParser.parse_args = parseargs
else:
    import argparse


if (3,) <= sys.version_info < (3, 2):
    import collections
    def callable(x):
        """ isinstance(x, collections.Callable)"""
        return isinstance(x, collections.Callable)
else:
    callable = callable

if sys.version_info < (3,0):
    unichr = unichr
else:
    unichr = chr
