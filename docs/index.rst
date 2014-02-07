Welcome to Cerberus
===================

Cerberus is an ISC Licensed validation tool for Python dictionaries.

Cerberus provides type checking and other base functionality out of the box and
is designed to be easily extensible, allowing for easy custom validation. It
has no dependancies and is thoroughly tested under Python 2.6, Python 2.7 and
Python 3.3.

    *CERBERUS, n. The watch-dog of Hades, whose duty it was to guard the
    entrance; everybody, sooner or later, had to go there, and nobody wanted to
    carry off the entrance. -Ambrose Bierce, The Devil's Dictionary*

Usage
------
You define a validation schema and pass it to an instance of the
:class:`~cerberus.Validator` class: ::

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

Then you simply invoke the :func:`~cerberus.Validator.validate` to validate
a dictionary against the schema. If validation succeeds, ``True`` is returned:

::

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True

Alternatively, you can pass both the dictionary and the schema to the
:func:`~cerberus.Validator.validate` method: ::

    >>> v = Validator()
    >>> v.validate(document, schema)
    True

Which can be handy if your schema is changing through the life of the
instance. ``False`` will be returned if validation fails. You can then access
the :func:`~cerberus.Validator.errors` property to get a list of validation
errors (see below).

.. versionchanged:: 0.4.1
    The Validator class is callable, allowing for the following shorthand
    syntax:

::

    >>> document = {'name': 'john doe'}
    >>> v(document)
    True


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
    {'age': 'min value is 10', 'name': 'must be of string type'}

You will still get :class:`~cerberus.SchemaError` and
:class:`~cerberus.ValidationError` exceptions. 

Allowing the unknown
~~~~~~~~~~~~~~~~~~~~
By default only keys defined in the schema are allowed: ::

    >>> schema = {'name': {'type': 'string', 'maxlength': 10}}
    >>> v.validate({'name': 'john', 'sex': 'M'})
    False
    >>> v.errors
    {'sex': 'unknown field'}

However, you can allow unknown key/value pairs by setting the ``allow_unknown``
option to ``True``: ::

    >>> v.allow_unknown = True
    >>> v.validate({'name': 'john', 'sex': 'M'})
    True

``allow_unknown`` can also be set at initialization: ::

    >>> v = Validator(schema=schema, allow_unknown=True)
    >>> v.validate({'name': 'john', 'sex': 'M'})
    True

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
                self._error(field, "Must be an odd number")

By subclassing Cerberus :class:`~cerberus.Validator` class and adding the custom
``_validate_<rulename>`` function, we just enhanced Cerberus to suit our needs.
The custom rule ``isodd`` is now available in our schema and, what really
matters, we can validate it: ::

    >>> v = MyValidator(schema)
    >>> v.validate({'oddity': 10})
    False
    >>> v.errors
    {'oddity': 'Must be an odd number'}

    >>> v.validate({'oddity': 9})
    True

.. _new-types:

Adding new data-types
'''''''''''''''''''''
Cerberus supports and validates several standard data types (see `type`_).
You can add and validate your own data types. For example `Eve
<https://python-eve.org>`_ (a tool for building and deploying proprietary REST
Web APIs) supports a custom ``objectid`` type, which is used to validate that
field values conform to the BSON/MongoDB ``ObjectId`` format.

You extend the supported set of data types by adding
a ``_validate_type_<typename>`` method to your own :class:`~cerberus.Validator`
subclass. This snippet, directly from Eve source, shows how the ``objectid``
has been implemented: ::

     def _validate_type_objectid(self, field, value):
        """ Enables validation for `objectid` schema attribute.

        :param field: field name.
        :param value: field value.
        """
        if not re.match('[a-f0-9]{24}', value):
            self._error(field, ERROR_BAD_TYPE % 'ObjectId')

.. versionadded:: 0.0.2

Validation Schema
-----------------
A validation schema is a dictionary. Schema keys are the keys allowed in
the target dictionary. Schema values express the rules that must be  matched by
the corresponding target values. ::

    >>> schema = {'name': {'type': 'string', 'maxlength': 10}}

In the example above we define a target dictionary with only one key, ``name``, 
which is expected to be a string not longer than 10 characters. Something like
``{'name': 'john doe'}`` would validate, while something like ``{'name': 'a
very long string'}`` or ``{'name': 99}`` would not. 

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
    * ``float``
    * ``number`` (integer or float)
    * ``boolean``
    * ``datetime``
    * ``dict``
    * ``list``

You can extend this list and support custom types, see :ref:`new-types`. 

.. note::

    Please note that type validation is performed before any other validation
    rule which might exist on the same field (only exception being the
    ``nullable`` rule). In the occurrence of a type failure subsequent
    validation rules on the field will be skipped and validation will continue
    on other fields. This allows to safely assume that field type is correct
    when other (standard or custom) rules are invoked.

.. versionchanged:: 0.4.0
   Type validation is always executed first, and blocks other field validation
   rules on failure.

.. versionchanged:: 0.3.0
   Added the ``float`` data type.

required
''''''''
If ``True`` the key/value pair is mandatory. Validation will fail when it is
missing, unless :func:`~cerberus.Validator.validate` is called with
``update=True``:

::

    >>> schema = {'name': {'required': True, 'type': 'string'}, 'age': {'type': 'integer'}}
    >>> v = Validator(schema)
    >>> document = {'age': 10}
    >>> v.validate(document)
    False
    >>> v.errors
    {'name': 'must be of string type'}

    >>> v.validate(document, update=True)
    True

.. note::

   String fields with empty values will still be validated, even when
   ``required`` is set to ``True``. If you don't want to accept empty values,
   see the empty_ rule. 

readonly
''''''''
If ``True`` the value is readonly. Validation will fail if this field is present
in the target dictionary.

nullable
''''''''
If ``True`` the field value can be set to ``None``. It is essentially the
functionality of the *ignore_non_values* parameter of the :ref:`validator`,
but allowing for more fine grained control down to the field level. ::

    >>> schema = {'a_nullable_integer': {'nullable': True, 'type': 'integer'}, 'an_integer': {'type': 'integer'}}
    >>> v = Validator(schema)

    >>> v.validate({'a_nullable_integer': 3})
    True
    >>> v.validate({'a_nullable_integer': None})
    True

    >>> v.validate({'an_integer': 3})
    True
    >>> v.validate({'an_integer': None})
    False
    >>> v.errors
    {'an_integer': 'must be of integer type'}

.. versionadded:: 0.3.0

minlength, maxlength 
'''''''''''''''''''' 
Minimum and maximum length allowed for ``string`` and ``list`` types. 

min, max
''''''''
Minimum and maximum value allowed for ``integer`` types.

allowed
'''''''
Allowed values for ``string``, ``list`` and ``int`` types. Validation will fail
if target values are not included in the allowed list.::

    >>> schema = {'role': {'type': 'list', 'allowed': ['agent', 'client', 'supplier']}}
    >>> v = Validator(schema)
    >>> v.validate({'role': ['agent', 'supplier']})
    True

    >>> v.validate({'role': ['intern']})
    False
    >>> v.errors
    {'role': "unallowed values ['intern']"}

    >>> schema = {'role': {'type': 'string', 'allowed': ['agent', 'client', 'supplier']}}
    >>> v = Validator(schema)
    >>> v.validate({'role': 'supplier'})
    True

    >>> v.validate({'role': 'intern'})
    False
    >>> v.errors
    {'role': 'unallowed value intern'}

    >>> schema = {'a_restricted_integer': {'type': 'integer', 'allowed': [-1, 0, 1]}}
    >>> v = Validator(schema)
    >>> v.validate({'a_restricted_integer': -1})
    True

    >>> v.validate({'a_restricted_integer': 2})
    False
    >>> v.errors
    {'a_restricted_unteger': 'unallowed value 2'}

.. versionchanged:: 0.5.1
   Added support for the ``int`` type.

empty
'''''
Only applies to string fields. If ``False`` validation will fail if the value
is empty. Defaults to ``True``. ::

    >>> schema = {'name': {'type': 'string', 'empty': False}}
    >>> document = {'name': ''}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    {'name': 'empty values not allowed'}

.. versionadded:: 0.0.3

.. _items_dict:

items (dict)
''''''''''''
.. deprecated:: 0.0.3
   Use :ref:`schema` instead.

When a dictionary, ``items`` defines the validation schema for items in
a ``list`` type: ::

    >>> schema = {'rows': {'type': 'list', 'items': {'sku': {'type': 'string'}, 'price': {'type': 'integer'}}}}
    >>> document = {'rows': [{'sku': 'KT123', 'price': 100}]}
    >>> v.validate(document, schema)
    True

.. note::

    The :ref:`items_dict` rule is deprecated, and will be removed in a future release.

items (list)
''''''''''''
When a list, ``items`` defines a list of values allowed in a ``list`` type of
fixed length: ::

    >>> schema = {'list_of_values': {'type': 'list', 'items': [{'type': 'string'}, {'type': 'integer'}]}}
    >>> document = {'list_of_values': ['hello', 100]}
    >>> v.validate(document, schema)
    True

See :ref:`schema` rule below for dealing with arbitrary length ``list`` types.

.. _schema:

schema
''''''
Validation schema for ``dict`` and ``list`` types. On dictionaries: ::

    >>> schema = {'a_dict': {'type': 'dict', 'schema': {'address': {'type': 'string'}, 'city': {'type': 'string', 'required': True}}}}
    >>> document = {'a_dict': {'address': 'my address', 'city': 'my town'}}
    >>> v.validate(document, schema)
    True

You can also use this rule to validate arbitrary length ``list`` items. ::

    >>> schema = {'a_list': {'type': 'list', 'schema': {'type': 'integer'}}}
    >>> document = {'a_list': [3, 4, 5]}
    >>> v.validate(document, schema)
    True

The `schema` rule on ``list`` types is also the prefered method for defining
and validating a list of dictionaries. ::

    >>> schema = {'rows': {'type': 'list', 'schema': {'type': 'dict', 'schema': {'sku': {'type': 'string'}, 'price': {'type': 'integer'}}}}}
    >>> document = {'rows': [{'sku': 'KT123', 'price': 100}]}
    >>> v.validate(document, schema)
    True

.. versionchanged:: 0.0.3
   Schema rule for ``list`` types of arbitrary length

.. _validator:

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

Installation
------------
Cerberus is on `PyPI <http://pypi.python.org/pypi/Cerberus>`_ so all you need
to do is: ::

    pip install cerberus

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
