Welcome to Cerberus
===================

Cerberus is an ISC Licensed validation tool for Python dictionaries.

Cerberus provides type checking and other base functionality out of the box and
is designed to be easily extensible, allowing for easy custom validation. It
has no dependancies and is thoroughly tested under Python 2.6 and 2.7. Support
for Python 3.x is planned.

.. note::
    Development of Cerberus is still underway, any feedback and contribution is
    welcome.

Usage
------
You define a validation schema and pass it to an instance of the
:class:`~cerberus.Validator` class: ::

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

Then you simply invoke the :func:`~cerberus.Validator.validate` or
:func:`~cerberus.Validator.validate_update` methods to validate a dictionary
against the schema. If validation succeeds, ``True`` is returned: ::

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True

Alternatively, you can pass both the dictionary and the schema to the
:func:`~cerberus.Validator.validate` method: ::

    >>> v = Validator()
    >>> v.validate(document, schema)
    True

Which can be handy if your schema is changing thorough the life of the
instance. ``False`` will be returned if validation fails. You can then access
the :func:`~cerberus.Validator.errors` property to get a list of validation
errors (see below).

Non-blocking
~~~~~~~~~~~~
Unlike other validation tools, Cerberus will not halt and raise an exception on
the first validation issue. The whole document will always be processed, and
``False`` will be returned if validation failed.  You can then access the
:func:`~cerberus.Validator.errors` method to obtain a list of issues.  ::

    >>> schema = {'name': {'type': 'string'}, 'age': {'type': 'integer', 'min': 10}}
    >>> document = {'name': 1337, 'age': 5}
    >>> v.validate(document, schema)
    False
    >>> v.errors
    ["min value for field 'age' is 10", "value of field 'name' must be of string type"]

You will still get :class:`~cerberus.SchemaError` and
:class:`~cerberus.ValidationError` exceptions. 

Custom validators
~~~~~~~~~~~~~~~~~
Cerberus makes custom validation simple. Suppose that in our specific and very
peculiar use case a certain value can only be expressed as an odd integer,
therefore we decide to add support for a new ``isodd`` rule to our validation
schema: ::

    >>> schema = {'oddity': {'isodd': True, 'type': 'integer'}}

This is how we would go to implement that: ::

    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_isodd(self, isodd, field, value):
            if isodd and not bool(value & 1):
                self._error("Value for field '%s' must be an odd number" % field)

By subclassing Cerberus :class:`~cerberus.Validator` class and adding the custom
``_validate_RULENAME`` function, we just enhanced Cerberus to suit our needs.
The custom rule ``ìsodd`` is now available in our schema and, what really
matters, we can validate it: ::

    >>> v = MyValidator(schema)
    >>> v.validate({'oddity': 10})
    False
    >>> v.errors
    ['Value for field 'oddity' must be an odd number']

    >>> v.validate({'oddity': 9})
    True

Validation Schema
-----------------
A validation schema is a dictionary. Schema keys are the keys allowed in
the target dictionary. Schema values express the rules that must be  matched by
the corresponding target values. ::

    >>> schema = {'name': {'type': 'string', 'maxlenght': 10}}

In the example above we define a target dictionary with only one key, ``name``, 
which is expected to be a string not longer than 10 characters. Something like
``{'name': 'john doe'}`` would validate, while something like ``{'name': 'a
very long string'}`` or ``{'name': 99}`` would not. 

Currently, only keys defined in the schema are allowed: ::

    >>> v.validate({'name': 'john', 'sex': 'M'})
    False
    >>> v.errors
    ["unknown field 'sex'"]

By definition all keys are optional unless the `required`_ rule is set for
a key.

Validation Rules
~~~~~~~~~~~~~~~~
The following rules are currently supported:

type
''''
Data type allowed for the key value. Can be one of the following:
    * ``string`` 
    * ``integer``
    * ``boolean``
    * ``datetime``
    * ``dict``
    * ``list``

required
''''''''
If True, the key/value pair is mandatory and validation will fail when
:func:`~cerberus.Validator.validate` is called.  Validation will still succeed
if the value is missing and :func:`~cerberus.Validator.validate_update` is
called instead.::

    >>> schema = {'name': {'required': True, 'type': 'string'}, 'age': {'type': 'integer'}}
    >>> document = {'age': 10}
    >>> v.validate(document)
    False
    >>> v.errors
    ["required field(s) are missing: 'name'"]

    >>> v.validate_update(document)
    True

readonly
''''''''
If True, the value is readonly. Validation will fail if this field is present
in the target dictionary.

minlength, maxlength
''''''''''''''''''''
Minimum and maximum length allowed for ``string`` types. 

min, max
''''''''
Minimum and maximum value allowed for ``ìnteger`` types.

allowed
'''''''
Allowed values for ``list`` types. Validation will fail if target values are
not included in the allowed list.::

    >>> schema = {'role': {'type': 'list', 'allowed': ['agent', 'client', 'supplier']}}
    >>> v.validate({'role': ['agent', 'supplier']})
    True

    >>> v.validate({'role': ['intern']})
    False
    >>> v.errors
    ["unallowed values ['intern'] for field 'role'"]

items (dict)
''''''''''''
When a dictionary, ``items`` defines the validation schema for items in
a ``list`` type:::

    >>> schema = {'rows': {'type': 'list','items': {'sku': {'type': 'string'}, 'price': {'type': 'integer'}}}}
    >>> document = {'rows': [{'sku': 'KT123', 'price': 100}]}
    >>> v.validate(document, schema)
    True

items (list)
''''''''''''
When a list, ``items`` defines a list of values allowed for the items in
a ``list`` type:::

    >>> schema = {'list_of_values': {'type': 'list', 'items': [{'type': 'string'}, {'type': 'integer'}]}}
    >>> document = {'list_of_values': ['hello', 100]}
    >>> v.validate(document, schema)
    True   

schema
''''''
Validation schema for ``dict`` types.::

    >>> schema = {'a_dict': {'type': 'dict', 'schema': {'address': {'type': 'string'}, 'city': {'type': 'string', 'required': True}}}}
    >>> document = {'a_dict': {'address': 'my address', 'city': 'my town'}}
    >>> v.validate(document, schema)
    True

Validator Class
---------------

.. autoclass:: cerberus.Validator
  :members:

Exceptions
----------
.. autoclass:: cerberus.SchemaError
  :members:

.. autoclass:: cerberus.ValidationError
  :members:

Testing
-------
.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

::

    >>> python setup.py test

Source Code
-----------
Source code is available at `GitHub
<https://github.com/nicolaiarocci/cerberus>`_.

Copyright Notice
----------------
This is an open source project by `Nicola Iarocci
<http://nicolaiarocci.com>`_. See the original `LICENSE
<https://github.com/nicolaiarocci/cerberus/blob/master/LICENSE>`_ for more
informations.
