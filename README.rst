Cerberus
========

.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is an ISC Licensed validation tool for Python dictionaries.

It provides type checking and basic functionality out of the box and is
designed to be easily extensible. It serves as the foundation block for Eve
validation module. Cerberus is tested for Python 2.6 and 2.7.

::

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Unlike other validator tools, Cerberus doesn't raise an exception at the first
validation error encountered. The whole document will be validated, and a list
of issues will be provided afterwards.

::

    >>> schema = {'name': {'type': 'string'}, 'age': {'type': 'integer', 'min': 10}}
    >>> document = {'name': 1337, 'age': 5}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    ["min value for field 'age' is 10", "value of field 'name' must be of string type"]

    

Work in progress
