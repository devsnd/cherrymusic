#!/bin/sh
if [[ $TRAVIS_PYTHON_VERSION = 2.6 ]]; then
    unit2 discover --failfast -s ./cherrymusicserver/test -t .
else
    python -m unittest discover --failfast -s ./cherrymusicserver/test -t .
fi
