Cerberus |latest-version|
=========================
|build-status| |python-support| 

Cerberus is a lightweight and extensible data validation library for Python.

.. code-block:: python

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Features
--------
Cerberus provides type checking and other base functionality out of the box and
is designed to be non-blocking and easily extensible, allowing for custom
validation. It has no dependancies and is thoroughly tested under Python 2.6,
Python 2.7, Python 3.3, Python 3.4, Python 3.5, PyPy and PyPy3.

Documentation
-------------
Complete documentation is available at http://python-cerberus.org

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

.. |latest-version| image:: https://img.shields.io/pypi/v/cerberus.svg
   :alt: Latest version on PyPI
   :target: https://pypi.python.org/pypi/cerberus
.. |build-status| image:: https://travis-ci.org/nicolaiarocci/cerberus.svg?branch=master
   :alt: Build status
   :target: https://travis-ci.org/nicolaiarocci/cerberus
.. |python-support| image:: https://img.shields.io/pypi/pyversions/cerberus.svg
   :target: https://pypi.python.org/pypi/cerberus
   :alt: Python versions
.. |license| image:: https://img.shields.io/pypi/l/cerberus.svg
   :alt: Software license
   :target: https://github.com/nicolaiarocci/cerberus/blob/master/LICENSE
