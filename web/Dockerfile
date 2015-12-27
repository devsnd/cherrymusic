FROM stackbrew/debian:jessie
RUN apt-get update && apt-get install -y python3 python3-pip libpq-dev python-dev

RUN echo deb http://www.deb-multimedia.org jessie main non-free >>/etc/apt/sources.list
RUN apt-get update && apt-get install -y --force-yes deb-multimedia-keyring
RUN apt-get update && apt-get install -y ffmpeg libmp3lame-dev libvorbis-dev flac lame

## dev only
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g bower less
RUN ln -s /usr/bin/nodejs /usr/bin/node
## 

ADD . /usr/src/app

WORKDIR /usr/src/app
RUN pip3 install -r requirements.txt
