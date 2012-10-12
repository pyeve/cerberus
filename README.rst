Cerberus
========
.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is an ISC Licensed validation tool for Python dictionaries.

::

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True

Features
--------
Cerberus provides type checking and other base functionality out of the box and
is designed to be easily extensible, allowing for custom validation. It has no
dependancies and is thoroughly tested under Python 2.6 and 2.7. Support for
Python 3.x is planned as well.

Non-blocking
~~~~~~~~~~~~
Cerberus will not halt execution and raise an exception on the first error
encountered. The whole document will always be processed, and a list of issues
will be provided at the end of the validation process.

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
Say that in our specific and very peculiar use case a certain value can only be
expressed as an odd integer, therefore we decide to add support for a new
``isodd`` rule in our validation schema: ::

    >>> schema = {'oddity': {'isodd': True, 'type': 'integer'}}

Of course we also want to validate incoming dictionaries against our schema: ::

    >>> v = MyValidator(schema)
    >>> v.validate({'oddity': 10})
    False
    >>> v.errors
    ['Value for field 'oddity' must be an odd number']

    >>> v.validate({'oddity': 9})
    True

This is how we would go to implement that: ::

    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_isodd(self, isodd, field, value):
            if isodd and not bool(value & 1):
                self._error("Value for field '%s' must be an odd number" % field)

As simple as that. By simply subclassing Cerberus' ``Validator`` class and
adding the ``_validate_RULENAME`` function, we enhanced Cerberus' functionality
to suit our needs. ``RULENAME`` (``ìsodd``) is now available in the schema
definition.

Work in Progress
----------------
Development of Cerberus is still underway and a complete documentation
is coming soon. Meanwhile, you can check the tests for a complete set of
examples and features. Any feedback is welcome.

Testing
-------
::

    >>> python setup.py test
