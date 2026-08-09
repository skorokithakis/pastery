Pastery
=======

[![CI](https://github.com/skorokithakis/pastery/actions/workflows/ci.yml/badge.svg)](https://github.com/skorokithakis/pastery/actions/workflows/ci.yml)

Pastery is the best pastebin in the world.


Installation
------------

To install:

~~~
$ poetry install --no-root
$ poetry run ./manage.py migrate
$ poetry run ./manage.py createsuperuser
$ poetry run ./manage.py runserver_plus
~~~

And just visit http://localhost:8000/, you're done.


Installation with Docker
------------------------

To run Pastery using Docker:

~~~
$ docker-compose up
(in another shell) $ docker-compose run web /code/manage.py createsuperuser
~~~

Visit http://localhost/, done.
