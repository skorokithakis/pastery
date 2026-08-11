Pastery
=======

[![CI](https://github.com/skorokithakis/pastery/actions/workflows/ci.yml/badge.svg)](https://github.com/skorokithakis/pastery/actions/workflows/ci.yml)

Pastery is the best pastebin in the world.


Installation
------------

To install:

~~~
$ uv sync
$ uv run ./manage.py migrate
$ uv run ./manage.py createsuperuser
$ uv run ./manage.py runserver
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
