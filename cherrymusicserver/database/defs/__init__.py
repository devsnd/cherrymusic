#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

_PACKAGEDIR = os.path.dirname(__file__)

cache = {}


def get(dbname):
    """The database definition as a ``dict``.

    Raises :
        ValueError : if there is no definition for that name
    """
    try:
        return cache[dbname]
    except KeyError:
        dbdef = _loaddef(dbname)
        return cache.setdefault(dbname, dbdef)


def getall():
    all = {}
    for name in _listnames(_PACKAGEDIR):
        all[name] = get(name)
    return all


def _loaddef(dbname):
    defdir = os.path.join(_PACKAGEDIR, dbname)
    if not os.path.isdir(defdir):
        raise ValueError("{0}: database not defined".format(defdir))
    dbdef = dict(
        (vnum, _loadversion(defdir, vnum)) for vnum in _listnames(defdir))
    return dbdef


def _loadversion(defdir, version):
    versiondef = {}
    versiondir = os.path.join(defdir, version)
    for name in _listnames(versiondir):
        fname = os.path.join(versiondir, name)
        with open(fname) as f:
            versiondef[name] = f.read()
    return versiondef


def _listnames(path):
    return (name for name in os.listdir(path) if not name.startswith('__'))
