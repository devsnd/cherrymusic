#!/bin/bash 

# Update Ubuntu 
apt-get update 
apt-get upgrade -y 

# Install Python Dependencies 
apt-get install python-pip -y 
pip install cherrypy 

# Install Cherry Music additional packages 
apt-get install imagemagick vorbis-tools lame flac -y 

# Start Cherry Pi 
python /var/www/cherrymusic --setup --port 8080 