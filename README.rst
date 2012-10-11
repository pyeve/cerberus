Cerberus
========

.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is an ISC Licensed validation tool for Python dictionaries.

It provides type checking and basic functionality out of the box and is
designed to be easily extensible. It serves as one of the foundation blocks for
the (yet to be released) Eve RESTful Web API. Cerberus is tested for Python 2.6
and 2.7. Support for Python 3.x is planned as well.

::

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Features
--------

Non-blocking
~~~~~~~~~~~~
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
issues.

Custom validators
~~~~~~~~~~~~~~~~~
Say that you need a certain value to be an odd integer. ::

    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_isodd(self, isodd, field, value):
            if isodd and not bool(value & 1):
                self._error("Value for field '%s' must be an odd number" % field)

You just subclass the Cerberus Validator and add ``_validate_RULENAME``, the
function that will validate your custom rule. ``RULENAME`` is now available in
your curstom schema definition:::

    >>> schema = {'age': {'isodd': True, 'type': 'integer'}}
    >>> v = MyValidator(schema)
    >>> v.validate({'age': 10})
    False
    >>> v.errors
    ['Value for field 'age' must be an odd number']

    >>> v.validate({'age': 9})
    True

Testing
-------
::

    >>> python setup.py test

Work in Progress
----------------
Development of Cerberus is still underway and a complete documentation
is coming soon. Meanwhile, you can check the tests for a complete set of
examples and features. Any feedback is welcome.

Stay tuned.
