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
