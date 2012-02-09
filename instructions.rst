##########################################################
Instructions for writing and installing a Geoanalytics app
##########################################################

This document will give you a general notion of how to write an app to be used
in the Geoanalytics framework.  It is not a complete documentation of
Geoanalytics, nor does it document the core components, but rather is intended
to get a developer oriented along the proper path to creating an application.
First off, if you've gotten this far, you will have run a single shell
command::

   $ geoanalytics_startapp APPNAME

This will provide you a fresh copy of the application structure in the current
directory, which is laid out as follows: 

   * ./APPNAME 
   * ./APPNAME/APPNAME
   * ./APPNAME/__init__.py
   * ./APPNAME/APPNAME/static
   * ./APPNAME/APPNAME/templates
   * ./APPNAME/APPNAME/testdata
   * ./APPNAME/APPNAME/models.py
   * ./APPNAME/APPNAME/views.py
   * ./APPNAME/APPNAME/tasks.py
   * ./APPNAME/APPNAME/regular_taskconfig.py
   * ./APPNAME/APPNAME/tests.py
   * ./APPNAME/APPNAME/up.py
   * ./APPNAME/APPNAME/down.py
   * ./APPNAME/APPNAME/urls.py
   * ./APPNAME/bin
   * ./APPNAME/CREDITS
   * ./APPNAME/doc
   * ./APPNAME/instructions.rst
   * ./APPNAME/README
   * ./APPNAME/requirements.txt
   * ./APPNAME/setup.py

APPNAME
=======

This is your new application directory.  No code should go here.

APPNAME/APPNAME
---------------

This is the main package directory for all your code.  It will create a package
called APPNAME which will be installed when you type ``python setup.py install``.

APPNAME/APPNAME/static
^^^^^^^^^^^^^^^^^^^^^^

Geoanalytics uses the `Django static files app <https://docs.djangoproject.com/en/1.3/ref/contrib/staticfiles/>`_ 
to find all the static files that a project exports.  Anything that doesn't use
the template language, such as static javascript, libraries, and homepages
should be stored here.

APPNAME/APPNAME/templates
^^^^^^^^^^^^^^^^^^^^^^^^^

All templates should be placed in this directory.  Django's template language
and application template loader will handle finding and using these templates.
Templates are generally filled in by views in the :file:`views.py` module.

   * `Template documentation <documentation>`_

APPNAME/APPNAME/testdata
^^^^^^^^^^^^^^^^^^^^^^^^

All test data source files should be placed in this directory.  It has no
special meaning now, but it may in the future.  

APPNAME/APPNAME/models.py
^^^^^^^^^^^^^^^^^^^^^^^^^

This holds `GeoDjango <https://docs.djangoproject.com/en/dev/ref/contrib/gis/>`_ 
and `MongoEngine <http://mongoengine.org>`_ ORM mappings.  Please see the
MongoEngine and GeoDjango documentation for more information on how to create
these models.  Also, if your application will not be using the default GeoDjango
database, you will want to add a line to :file:`settings.py` in the virtualenv
that routes the data to the correct database.  This is especially important for
applications with particularly large or large numbers of tables, or apps that
use databases from other sites.

APPNAME/APPNAME/views.py
^^^^^^^^^^^^^^^^^^^^^^^^

This holds views.  Views take HTTP requests and parameters and return
responses.  If you have need for creating custom pages for your app beyond
exposing your models via WMS, WFS, WCS, or JSON then you will want to define
some views here.  Otherwise the generic views provided by Django or Geoanalytics will
suffice.  For more on views, see:

   * `Django views documentation <https://docs.djangoproject.com/en/dev/topics/http/views/>`_
   * `Django generic views <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_
   * `Geoanalytics views documentation <http://geoanalytics.renci.org/docs>`_

APPNAME/APPNAME/tasks.py
^^^^^^^^^^^^^^^^^^^^^^^^

This holds tasks for the Celery distributed task queue.  These can be regularly
executed tasks or they can be one-off, on demand tasks.  

   * `Writing celery tasks <http://celery.readthedocs.org/en/latest/userguide/tasks.html>`_

APPNAME/APPNAME/regular_taskconfig.py
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This holds a dictionary called CELERYBEAT_SCHEDULE which contains the tasks to
be executed at regular intervals and how often they should be executed.  

   * `Periodic tasks in Celery <http://celery.readthedocs.org/en/latest/userguide/periodic-tasks.html>`_

APPNAME/APPNAME/tests.py
^^^^^^^^^^^^^^^^^^^^^^^^

Django has a fairly generic testing framework which can be run using the
manage.py script in the virtualenv-ironment's Django root directory.  Add any
and all test cases here.  All test cases follow the rules for python's
`unittest2 unit testing framework <https://docs.djangoproject.com/en/dev/topics/testing/>`_ .

APPNAME/APPNAME/up.py and down.py
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is just a "best practice" file.  The idea is that :file:`tests.py` should
import this module and call :fun:`up.up()` in :method:`setUp()` to load test
data and :fun:`down.down()` in :method:`tearDown()` to destroy it.

APPNAME/APPNAME/urls.py
^^^^^^^^^^^^^^^^^^^^^^^

This file contains all the view - url mappings using either Django or
Geoanalytics generic views or the views that you setup in :file:`views.py` .

APPNAME/APPNAME/bin
^^^^^^^^^^^^^^^^^^^

This should contain any utilities and executables you want to install along
with your application.  These will go in the virtualenv-ironment's :file:`bin/`
directory.

APPNAME/APPNAME/CREDITS
^^^^^^^^^^^^^^^^^^^^^^^

Give yourself some credit.  You've gotten this far...

APPNAME/doc
^^^^^^^^^^^

This contains a `Sphinx <http://sphinx.pocoo.org/>`_ documentation tree.  This
will be processed, and can be published statically.  There is intent, however,
to provide a "documentation" app that harvests this automatically and publishes
it.  

APPNAME/README
^^^^^^^^^^^^^^

Please provide an informative readme.  It's just good manners.

APPNAME/requirements.txt
^^^^^^^^^^^^^^^^^^^^^^^^

The installer executes ``pip install $name`` for every line in requirements.txt
inside the current virtualenv-ironment.

APPNAME/APPNAME/setup.py
^^^^^^^^^^^^^^^^^^^^^^^^

This script does all of the installation for you.  To install your application,
activate a virtualenv-ironment containing the installation you want to run on
and type::

   $ python setup.py install




