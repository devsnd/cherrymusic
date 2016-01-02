CherryMusic
===========

This is a rewrite of CherryMusic to be based on django.

Setup
-----

Configure `config.yml` with your music directories:
* One path:
```docker-compose
web:
  volumes:
    - /home/user/My Music:/usr/src/app/music:ro
```
* Multiple paths:
```docker-compose
web:
  volumes:
    - /home/user/Classic Music:/usr/src/app/music/Classic:ro
    - /home/user/Punk Music:/usr/src/app/music/Punk:ro
```

Install dependencies:
* docker
* docker-compose

Create containers:
```bash
docker-compose build
docker-compose up -d
```

Initialice database:
```bash
docker-compose run --rm web python3 manage.py migrate auth
docker-compose run --rm web python3 manage.py migrate 
```

Default admin user: `admin/admin`

Reinstall cherrymusic
---------------------
```bash
docker-compose stop
docker-compose rm
```
And then reinstall.


Update cherrymusic
------------------
```bash
docker-compose stop
docker-compose rm web nginx
docker-compose build
docker-compose up -d
```

Development frotent
-------------------
To install and run development containers:
```bash
docker-compose stop
docker-compose rm web nginx
docker-compose -f docker-compose.yml -f development.yml build
docker-compose -f docker-compose.yml -f development.yml up -d
```

Install bower components:
```bash
docker-compose run --rm web python3 manage.py bower_install
```
Update static files
-------------------
In development mode:

In `./web`:
```bash
docker-compose run --rm web python3 manage.py collectstatic
```
