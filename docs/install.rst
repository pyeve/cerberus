Cerberus Installation
=====================

This part of the documentation covers the installation of Cerberus. The first
step to using any software package is getting it properly installed.

Stable Version
--------------
Cerberus is on `PyPI <https://pypi.python.org/pypi/Cerberus>`_ so all you need
to do is:

.. code-block:: console

    $ pip install cerberus

Development Version
-------------------
Cerberus is actively developed on GitHub, where the code is `always available
<https://github.com/pyeve/cerberus>`_. If you want to work with the
development version, there are two ways: you can either let `pip` pull
in the development version, or you can tell it to operate on a git checkout.
Either way, virtualenv is recommended.

Get the git checkout in a new virtualenv and run in development mode.

.. code-block:: console

    $ git clone http://github.com/pyeve/cerberus.git
    Initialized empty Git repository in ~/dev/cerberus.git/
    $ cd cerberus
    $ virtualenv venv --distribute
    New python executable in venv/bin/python
    Installing distribute............done.
    $ . venv/bin/activate
    $ python setup.py install
    ...
    Finished processing dependencies for Cerberus

This will pull in the dependencies and activate the git head as the current
version inside the virtualenv.  Then all you have to do is run ``git pull
origin`` to update to the latest version.

To just get the development version without git, do this instead:

.. code-block:: console

    $ mkdir cerberus
    $ cd cerberus
    $ virtualenv venv --distribute
    $ . venv/bin/activate
    New python executable in venv/bin/python
    Installing distribute............done.
    $ pip install git+git://github.com/pyeve/cerberus.git
    ...
    Cleaning up...

And you're done!
