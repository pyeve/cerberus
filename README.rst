Cerberus
========
.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is an ISC Licensed validation tool for Python dictionaries.

.. code-block:: pycon

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Features
--------
Cerberus provides type checking and other base functionality out of the box and
is designed to be non-blocking and easily extensible, allowing for custom
validation. It has no dependancies and is thoroughly tested under Python 2.6,
Python 2.7, Python 3.3, Python 3.4, PyPy and PyPy3.

Documentation
-------------
Complete documentation is available at http://cerberus.readthedocs.org

Installation
------------
Cerberus is on PyPI so all you need is:

.. code-block:: console

    $ pip install cerberus

Testing
-------
Just run:

.. code-block:: console

    $ python setup.py test

Or you can use tox to run the tests under all supported Python versions. Make
sure the required python versions are installed and run:

.. code-block:: console

    $ pip install tox  # first time only
    $ tox

Contributing
------------
Please see the `Contribution Guidelines`_.


Copyright
---------
Cerberus is an open source project by `Nicola Iarocci
<http://nicolaiarocci.com>`_. See the original `LICENSE
<https://github.com/nicolaiarocci/cerberus/blob/master/LICENSE>`_ for more
informations.

.. _`Contribution Guidelines`: https://github.com/nicolaiarocci/cerberus/blob/master/CONTRIBUTING.rst
