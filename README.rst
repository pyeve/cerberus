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
Python 2.7, Python 3.3, Python 3.4, Python 3.5, Python 3.6, PyPy and PyPy3.

Funding
-------
Cerberus is a open source, collaboratively funded project. If you run
a business and are using Cerberus in a revenue-generating product, it would
make business sense to sponsor its development: it ensures the project that
your product relies on stays healthy and actively maintained. Individual users
are also welcome to make a recurring pledge or a one time donation if Cerberus
has helped you in your work or personal projects. 

Every single sign-up makes a significant impact towards making Eve possible. To
learn more, check out our `funding page`_.

Documentation
-------------
Complete documentation is available at http://docs.python-cerberus.org

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
<https://github.com/pyeve/cerberus/blob/master/LICENSE>`_ for more
informations.

.. _`Contribution Guidelines`: https://github.com/pyeve/cerberus/blob/master/CONTRIBUTING.rst

.. |latest-version| image:: https://img.shields.io/pypi/v/cerberus.svg
   :alt: Latest version on PyPI
   :target: https://pypi.python.org/pypi/cerberus
.. |build-status| image:: https://travis-ci.org/pyeve/cerberus.svg?branch=master
   :alt: Build status
   :target: https://travis-ci.org/pyeve/cerberus
.. |python-support| image:: https://img.shields.io/pypi/pyversions/cerberus.svg
   :target: https://pypi.python.org/pypi/cerberus
   :alt: Python versions
.. |license| image:: https://img.shields.io/pypi/l/cerberus.svg
   :alt: Software license
   :target: https://github.com/pyeve/cerberus/blob/master/LICENSE
