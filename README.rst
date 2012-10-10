Cerberus
========

.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is an ISC Licensed validation tool for Python dictionaries.

It provides type checking and basic functionality out of the box and is
designed to be easily extensible. It serves as the foundation block for Eve
validation module. Cerberus is tested for Python 2.6 and 2.7.

Features
--------
::

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Unlike other validator tools, Cerberus will not raise an exception when the
first validation error is encountered. The whole document will always get
validated, and a list of issues will be provided afterwards.

::

    >>> schema = {'name': {'type': 'string'}, 'age': {'type': 'integer', 'min': 10}}
    >>> document = {'name': 1337, 'age': 5}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    ["min value for field 'age' is 10", "value of field 'name' must be of string type"]

You will still get SchemaError and ValidationError exceptions on initialization
errors.

Testing
-------
::

    >>> python setup.py test

Work in Progress
----------------
Development of Cerberus is still underway, and a complete documentation is
coming soon. Meanwhile, you can check the tests for a complete set of examples
and features.


