#!/bin/sh
python ./setup.py sdist
sudo pacman -R python-cherrymusic
cd dist
makepkg -f
sudo pacman -U python-cherrymusic-0.2-1-any.pkg.tar.xz
