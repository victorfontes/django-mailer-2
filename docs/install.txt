============
Installation
============

An obvious prerequisite of Django Mailer 2 is Django - 1.1 is the
minimum supported version.


Installing django-mailer-2
==========================

Download and install from http://github.com/SmileyChris/django-mailer-2.git

If you're using pip__ and a virtual environment, this usually looks like::

    pip install -e git+http://github.com/SmileyChris/django-mailer-2.git#egg=django-mailer-2

.. __: http://pip.openplans.org/

Or for a manual installation, once you've downloaded the package, unpack it
and run the ``setup.py`` installation script::

    python setup.py install


Configuring your project
========================

In your Django project's settings module, add django_mailer to your
``INSTALLED_APPS`` setting::
    
    INSTALLED_APPS = (
        ...
        'django_mailer',
    )

Note that django mailer doesn't implicitly queue all django mail (unless you
tell it to). More details can be found in the usage documentation.
