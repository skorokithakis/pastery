Pastery
=======

Pastery is the best pastebin in the world.


Installation
------------

To install:

~~~
$ virtualenv env
$ source env/bin/activate
$ pip install -Ur requirements.txt
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver_plus
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
