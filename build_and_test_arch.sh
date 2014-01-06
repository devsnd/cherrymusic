#!/bin/sh
VERSION=`python -c "import cherrymusicserver; print(cherrymusicserver.__version__)"`
python ./setup.py sdist
sudo pacman -R python-cherrymusic
cd dist
makepkg -f
sudo pacman -U python-cherrymusic-$VERSION-any.pkg.tar.xz
