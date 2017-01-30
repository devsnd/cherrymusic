#!/usr/bin/python3
# -*- coding: utf-8 -*-
from collections import *


if 'OrderedDict' not in dir():
    from _backported import Counter
    from _backported import OrderedDict
