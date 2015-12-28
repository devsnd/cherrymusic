CherryMusic
===========

This is a rewrite of CherryMusic to be based on django.

Development setup
-----------------

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

Update static files
-------------------
Dependencies:
* Bower
* Less

In `./web`:
```bash
python manage.py collectstatic
```

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
Install bower components:
```bash
docker-compose run --rm web python3 manage.py bower_install
```
