Validation Rules
================

allow_unknown
-------------
This can be used in conjunction with the  `schema <schema_dict-rule>`_ rule
when validating a mapping in order to set the
:attr:`~cerberus.Validator.allow_unknown` property of the validator for the
subdocument.
For a full alaboration refer to :ref:`this paragraph <allowing-the-unknown>`.

allowed
-------
If the target value is an :term:`iterable`, all its members must be in the
list of allowed values. Other types of target values will validate if the
value is in that list.

.. doctest::

    >>> v.schema = {'role': {'type': 'list', 'allowed': ['agent', 'client', 'supplier']}}
    >>> v.validate({'role': ['agent', 'supplier']})
    True

    >>> v.validate({'role': ['intern']})
    False
    >>> v.errors
    {'role': ["unallowed values ['intern']"]}

    >>> v.schema = {'role': {'type': 'string', 'allowed': ['agent', 'client', 'supplier']}}
    >>> v.validate({'role': 'supplier'})
    True

    >>> v.validate({'role': 'intern'})
    False
    >>> v.errors
    {'role': ['unallowed value intern']}

    >>> v.schema = {'a_restricted_integer': {'type': 'integer', 'allowed': [-1, 0, 1]}}
    >>> v.validate({'a_restricted_integer': -1})
    True

    >>> v.validate({'a_restricted_integer': 2})
    False
    >>> v.errors
    {'a_restricted_integer': ['unallowed value 2']}

.. versionchanged:: 0.5.1
   Added support for the ``int`` type.

allof
-----
Validates if *all* of the provided constraints validates the field. See `\*of-rules`_ for details.

.. versionadded:: 0.9

anyof
-----
Validates if *any* of the provided constraints validates the field. See `\*of-rules`_ for details.

.. versionadded:: 0.9

.. _dependencies:

dependencies
------------
This rule allows to define either a single field name, a sequence of field
names or a :term:`mapping` of field names and a sequence of allowed values as
required in the document if the field defined upon is present in the document.

.. doctest::

   >>> schema = {'field1': {'required': False}, 'field2': {'required': False, 'dependencies': 'field1'}}
   >>> document = {'field1': 7}
   >>> v.validate(document, schema)
   True

   >>> document = {'field2': 7}
   >>> v.validate(document, schema)
   False

   >>> v.errors
   {'field2': ["field 'field1' is required"]}


When multiple field names are defined as dependencies, all of these must be
present in order for the target field to be validated.

.. doctest::

   >>> schema = {'field1': {'required': False}, 'field2': {'required': False},
   ...           'field3': {'required': False, 'dependencies': ['field1', 'field2']}}
   >>> document = {'field1': 7, 'field2': 11, 'field3': 13}
   >>> v.validate(document, schema)
   True

   >>> document = {'field2': 11, 'field3': 13}
   >>> v.validate(document, schema)
   False

   >>> v.errors
   {'field3': ["field 'field1' is required"]}

When a mapping is provided, not only all dependencies must be present,
but also any of their allowed values must be matched.

.. doctest::

   >>> schema = {'field1': {'required': False},
   ...           'field2': {'required': True, 'dependencies': {'field1': ['one', 'two']}}}

   >>> document = {'field1': 'one', 'field2': 7}
   >>> v.validate(document, schema)
   True

   >>> document = {'field1': 'three', 'field2': 7}
   >>> v.validate(document, schema)
   False
   >>> v.errors
   {'field2': ["depends on these values: {'field1': ['one', 'two']}"]}

   >>> # same as using a dependencies list
   >>> document = {'field2': 7}
   >>> v.validate(document, schema)
   False
   >>> v.errors
   {'field2': ["depends on these values: {'field1': ['one', 'two']}"]}


   >>> # one can also pass a single dependency value
   >>> schema = {'field1': {'required': False}, 'field2': {'dependencies': {'field1': 'one'}}}
   >>> document = {'field1': 'one', 'field2': 7}
   >>> v.validate(document, schema)
   True

   >>> document = {'field1': 'two', 'field2': 7}
   >>> v.validate(document, schema)
   False

   >>> v.errors
   {'field2': ["depends on these values: {'field1': 'one'}"]}

Declaring dependencies on subdocument fields with dot-notation is also
supported:

.. doctest::

   >>> schema = {
   ...   'test_field': {'dependencies': ['a_dict.foo', 'a_dict.bar']},
   ...   'a_dict': {
   ...     'type': 'dict',
   ...     'schema': {
   ...       'foo': {'type': 'string'},
   ...       'bar': {'type': 'string'}
   ...     }
   ...   }
   ... }

   >>> document = {'test_field': 'foobar', 'a_dict': {'foo': 'foo'}}
   >>> v.validate(document, schema)
   False

   >>> v.errors
   {'test_field': ["field 'a_dict.bar' is required"]}

When a subdocument is processed the lookup for a field in question starts at
the level of that document. In order to address the processed document as
root level, the declaration has to start with a ``^``. An occurance of two
initial carets (``^^``) is interpreted as a literal, single ``^`` with no
special meaning.

.. doctest::

   >>> schema = {
   ...   'test_field': {},
   ...   'a_dict': {
   ...     'type': 'dict',
   ...     'schema': {
   ...       'foo': {'type': 'string'},
   ...       'bar': {'type': 'string', 'dependencies': '^test_field'}
   ...     }
   ...   }
   ... }

   >>> document = {'a_dict': {'bar': 'bar'}}
   >>> v.validate(document, schema)
   False

   >>> v.errors
   {'a_dict': [{'bar': ["field '^test_field' is required"]}]}

.. note::
   If you want to extend semantics of the dot-notation, you can
   :doc:`override <customize>` the :meth:`~cerberus.Validator._lookup_field`
   method.

.. note::
   The evaluation of this rule does not consider any constraints defined with
   the :ref:`required` rule.

.. versionchanged:: 1.0.2 Support for absolute addressing with ``^``.

.. versionchanged:: 0.8.1 Support for sub-document fields as dependencies.

.. versionchanged:: 0.8 Support for dependencies as a dictionary.

.. versionadded:: 0.7

empty
-----
If ``False`` validation of an :term:`iterable` value will fail if it is empty.
Setting it to ``True`` manually is pointless as it behaves like omitting the
rule at all.

.. doctest::

    >>> schema = {'name': {'type': 'string', 'empty': False}}
    >>> document = {'name': ''}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    {'name': ['empty values not allowed']}

.. versionadded:: 0.0.3

excludes
--------
You can declare fields to excludes others:

.. doctest::

    >>> v = Validator()
    >>> schema = {'this_field': {'type': 'dict',
    ...                          'excludes': 'that_field'},
    ...           'that_field': {'type': 'dict',
    ...                          'excludes': 'this_field'}}
    >>> v.validate({'this_field': {}, 'that_field': {}}, schema)
    False
    >>> v.validate({'this_field': {}}, schema)
    True
    >>> v.validate({'that_field': {}}, schema)
    True
    >>> v.validate({}, schema)
    True


You can require both field to build an exclusive `or`:

.. doctest::

    >>> v = Validator()
    >>> schema = {'this_field': {'type': 'dict',
    ...                          'excludes': 'that_field',
    ...                          'required': True},
    ...           'that_field': {'type': 'dict',
    ...                          'excludes': 'this_field',
    ...                          'required': True}}
    >>> v.validate({'this_field': {}, 'that_field': {}}, schema)
    False
    >>> v.validate({'this_field': {}}, schema)
    True
    >>> v.validate({'that_field': {}}, schema)
    True
    >>> v.validate({}, schema)
    False


You can also pass multiples fields to exclude in a list :

.. doctest::

   >>> schema = {'this_field': {'type': 'dict',
   ...                          'excludes': ['that_field', 'bazo_field']},
   ...           'that_field': {'type': 'dict',
   ...                          'excludes': 'this_field'},
   ...           'bazo_field': {'type': 'dict'}}
   >>> v.validate({'this_field': {}, 'bazo_field': {}}, schema)
   False

forbidden
---------

Opposite to `allowed`_ this validates if a value is any but one of the defined
values:

.. doctest::

   >>> schema = {'user': {'forbidden': ['root', 'admin']}}
   >>> document = {'user': 'root'}
   >>> v.validate(document, schema)
   False

.. versionadded:: 1.0

items
-----
Validates the items of any iterable against a sequence of rules that must
validate each index-correspondent item. The items will only be evaluated if
the given iterable's size matches the definition's.

.. doctest::

   >>> schema = {'list_of_values': {'type': 'list', 'items': [{'type': 'string'}, {'type': 'integer'}]}}
   >>> document = {'list_of_values': ['hello', 100]}
   >>> v.validate(document, schema)
   True
   >>> document = {'list_of_values': [100, 'hello']}
   >>> v.validate(document, schema)
   False

See `schema (list)`_ rule for dealing with arbitrary length ``list`` types.

.. _keyschema-rule:

keyschema
---------
Validation schema for all keys of a :term:`mapping`.

.. doctest::

    >>> schema = {'a_dict': {'type': 'dict', 'keyschema': {'type': 'string', 'regex': '[a-z]+'}}}
    >>> document = {'a_dict': {'key': 'value'}}
    >>> v.validate(document, schema)
    True

    >>> document = {'a_dict': {'KEY': 'value'}}
    >>> v.validate(document, schema)
    False

.. versionadded:: 0.9

.. versionchanged:: 1.0
   Renamed from ``propertyschema`` to ``keyschema``

min, max
--------
Minimum and maximum value allowed for any types that implement comparison operators.

.. versionchanged:: 1.0
  Allows any type to be compared.

.. versionchanged:: 0.7
  Added support for ``float`` and ``number`` types.

minlength, maxlength
--------------------
Minimum and maximum length allowed for iterables.

noneof
------

Validates if *none* of the provided constraints validates the field. See `\*of-rules`_ for details.

.. versionadded:: 0.9

nullable
--------
If ``True`` the field value is allowed to be :obj:`None`. The rule will be
checked on every field, regardless it's defined or not. The rule's constraint
defaults ``False``.

.. doctest::

   >>> v.schema = {'a_nullable_integer': {'nullable': True, 'type': 'integer'}, 'an_integer': {'type': 'integer'}}

   >>> v.validate({'a_nullable_integer': 3})
   True
   >>> v.validate({'a_nullable_integer': None})
   True

   >>> v.validate({'an_integer': 3})
   True
   >>> v.validate({'an_integer': None})
   False
   >>> v.errors
   {'an_integer': ['null value not allowed']}

.. versionchanged:: 0.7 ``nullable`` is valid on fields lacking type definition.
.. versionadded:: 0.3.0


\*of-rules
----------

These rules allow you to list multiple sets of rules to validate against. The
field will be considered valid if it validates against the set in the list
according to the prefixes logics ``all``, ``any``, ``one`` or ``none``.

==========  ====================================================================
``allof``   Validates if *all* of the provided constraints validates the field.
``anyof``   Validates if *any* of the provided constraints validates the field.
``noneof``  Validates if *none* of the provided constraints validates the field.
``oneof``   Validates if *exactly one* of the provided constraints applies.
==========  ====================================================================

For example, to verify that a property is a number between 0 and 10 or 100 and
110, you could do the following:

.. doctest::

    >>> schema = {'prop1':
    ...           {'type': 'number',
    ...            'anyof':
    ...            [{'min': 0, 'max': 10}, {'min': 100, 'max': 110}]}}

    >>> document = {'prop1': 5}
    >>> v.validate(document, schema)
    True

    >>> document = {'prop1': 105}
    >>> v.validate(document, schema)
    True

    >>> document = {'prop1': 55}
    >>> v.validate(document, schema)
    False
    >>> v.errors   # doctest: +SKIP
    {'prop1': {'anyof': 'no definitions validated', 'definition 1': 'min value is 100', 'definition 0': 'max value is 10'}}

The ``anyof`` rule works by creating a new instance of a schema for each item
in the list. The above schema is equivalent to creating two separate schemas:

.. doctest::

    >>> schema1 = {'prop1': {'type': 'number', 'min':   0, 'max':  10}}
    >>> schema2 = {'prop1': {'type': 'number', 'min': 100, 'max': 110}}

    >>> document = {'prop1': 5}
    >>> v.validate(document, schema1) or v.validate(document, schema2)
    True

    >>> document = {'prop1': 105}
    >>> v.validate(document, schema1) or v.validate(document, schema2)
    True

    >>> document = {'prop1': 55}
    >>> v.validate(document, schema1) or v.validate(document, schema2)
    False

.. versionadded:: 0.9

\*of-rules typesaver
....................

You can concatenate any of-rule with an underscore and another rule with a
list of rule-values to save typing:

.. testcode::

    {'foo': {'anyof_type': ['string', 'integer']}}
    # is equivalent to
    {'foo': {'anyof': [{'type': 'string'}, {'type': 'integer'}]}}

Thus you can use this to validate a document against several schemas without
implementing your own logic:

.. testsetup::

    employees = ()

.. doctest::

    >>> schemas = [{'department': {'required': True, 'regex': '^IT$'}, 'phone': {'nullable': True}},
    ...            {'department': {'required': True}, 'phone': {'required': True}}]
    >>> emloyee_vldtr = Validator({'employee': {'oneof_schema': schemas, 'type': 'dict'}}, allow_unknown=True)
    >>> invalid_employees_phones = []
    >>> for employee in employees:
    ...     if not employee_vldtr.validate(employee):
    ...         invalid_employees_phones.append(employee)

.. versionadded: 1.0

oneof
-----

Validates if *exactly one* of the provided constraints applies. See `\*of-rules`_ for details.

.. versionadded:: 0.9

.. _readonly:

readonly
--------
If ``True`` the value is readonly. Validation will fail if this field is
present in the target dictionary. This is useful, for example, when receiving
a payload which is to be validated before it is sent to the datastore. The field
might be provided by the datastore, but should not writable.

.. versionchanged:: 1.0.2
   Can be used in conjunction with ``default`` and ``default_setter``,
   see :ref:`default-values`.

regex
-----
Validation will fail if field value does not match the provided regular
expression. It is only tested on string values.

.. doctest::

    >>> schema = {'email': {'type': 'string', 'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'}}
    >>> document = {'email': 'john@example.com'}
    >>> v.validate(document, schema)
    True

    >>> document = {'email': 'john_at_example_dot_com'}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    {'email': ["value does not match regex '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'"]}

For details on regular expression syntax, see the documentation on the standard
library's :mod:`re`-module. Mind that you can set flags as part of the
expression, look for ``(?aiLmsux)`` in that document.

.. versionadded:: 0.7

.. _required:

required
--------
If ``True`` the field is mandatory. Validation will fail when it is missing,
unless :meth:`~cerberus.Validator.validate` is called with ``update=True``:

.. doctest::

    >>> v.schema = {'name': {'required': True, 'type': 'string'}, 'age': {'type': 'integer'}}
    >>> document = {'age': 10}
    >>> v.validate(document)
    False
    >>> v.errors
    {'name': ['required field']}

    >>> v.validate(document, update=True)
    True

.. note::

   String fields with empty values will still be validated, even when
   ``required`` is set to ``True``. If you don't want to accept empty values,
   see the empty_ rule.

.. note::
   The evaluation of this rule does not consider any constraints defined with
   the :ref:`dependencies` rule.

.. versionchanged:: 0.8
   Check field dependencies.

.. _schema_dict-rule:

schema (dict)
-------------
If a field for which a ``schema``-rule is defined has a *mapping* as value,
that mapping will be validated against the schema that is provided as
constraint.

.. doctest::

    >>> schema = {'a_dict': {'type': 'dict', 'schema': {'address': {'type': 'string'},
    ...                                                 'city': {'type': 'string', 'required': True}}}}
    >>> document = {'a_dict': {'address': 'my address', 'city': 'my town'}}
    >>> v.validate(document, schema)
    True

.. note::

    To validate *arbitrary keys* of a mapping, see `keyschema`_, resp.
    `valueschema`_ for validating *arbitrary values* of a mapping.

schema (list)
-------------
If ``schema``-validation encounters an arbritrary sized *sequence* as value,
all items of the sequence will be validated against the rules provided in
``schema``'s constraint.

.. doctest::

   >>> schema = {'a_list': {'type': 'list', 'schema': {'type': 'integer'}}}
   >>> document = {'a_list': [3, 4, 5]}
   >>> v.validate(document, schema)
   True

The `schema` rule on ``list`` types is also the preferred method for defining
and validating a list of dictionaries.

.. note::

    Using this rule should be accompanied with a ``type``-rule explicitly
    restricting the field to the ``list``-type like in the example. Otherwise
    false results can be expected when a mapping is validated against this rule
    with constraints for a sequence.

.. doctest::

   >>> schema = {'rows': {'type': 'list',
   ...                    'schema': {'type': 'dict', 'schema': {'sku': {'type': 'string'},
   ...                                                          'price': {'type': 'integer'}}}}}
   >>> document = {'rows': [{'sku': 'KT123', 'price': 100}]}
   >>> v.validate(document, schema)
   True

.. versionchanged:: 0.0.3
  Schema rule for ``list`` types of arbitrary length

.. _type:

type
----
Data type allowed for the key value. Can be one of the following names:

.. list-table::
   :header-rows: 1

   * - Type Name
     - Python 2 Type
     - Python 3 Type
   * - ``boolean``
     - :class:`py2:bool`
     - :class:`py3:bool`
   * - ``binary``
     - :class:`py2:bytes` [#]_, :class:`py2:bytearray`
     - :class:`py3:bytes`, :class:`py3:bytearray`
   * - ``date``
     - :class:`py2:datetime.date`
     - :class:`py3:datetime.date`
   * - ``datetime``
     - :class:`py2:datetime.datetime`
     - :class:`py3:datetime.datetime`
   * - ``dict``
     - :class:`py2:collections.Mapping`
     - :class:`py3:collections.abc.Mapping`
   * - ``float``
     - :class:`py2:float`
     - :class:`py3:float`
   * - ``integer``
     - :class:`py2:int`, :class:`py2:long`
     - :class:`py3:int`
   * - ``list``
     - :class:`py2:collections.Sequence`, excl. ``string``
     - :class:`py3:collections.abc.Sequence`, excl. ``string``
   * - ``number``
     - :class:`py2:float`, :class:`py2:int`, :class:`py2:long`, excl. :class:`py2:bool`
     - :class:`py3:float`, :class:`py3:int`, excl. :class:`py3:bool`
   * - ``set``
     - :class:`py2:set`
     - :class:`py3:set`
   * - ``string``
     - :func:`py2:basestring`
     - :class:`py3:str`

You can extend this list and support :ref:`custom types <new-types>`.

A list of types can be used to allow different values:

.. doctest::

    >>> v.schema = {'quotes': {'type': ['string', 'list']}}
    >>> v.validate({'quotes': 'Hello world!'})
    True
    >>> v.validate({'quotes': ['Do not disturb my circles!', 'Heureka!']})
    True

.. doctest::

    >>> v.schema = {'quotes': {'type': ['string', 'list'], 'schema': {'type': 'string'}}}
    >>> v.validate({'quotes': 'Hello world!'})
    True
    >>> v.validate({'quotes': [1, 'Heureka!']})
    False
    >>> v.errors
    {'quotes': [{0: ['must be of string type']}]}

.. note::

    While the ``type`` rule is not required to be set at all, it is not
    encouraged to leave it unset especially when using more complex rules such
    as ``schema``. If you decide you still don't want to set an explicit type,
    rules such as ``schema`` are only applied to values where the rules can
    actually be used (such as ``dict`` and ``list``). Also, in the case of
    ``schema``, cerberus will try to decide if a ``list`` or a ``dict`` type
    rule is more appropriate and infer it depending on what the ``schema`` rule
    looks like.

.. note::

    Please note that type validation is performed before most others which
    exist for the same field (only `nullable`_ and `readonly`_ are considered
    beforehand). In the occurrence of a type failure subsequent validation
    rules on the field will be skipped and validation will continue on other
    fields. This allows to safely assume that field type is correct when other
    (standard or custom) rules are invoked.

.. versionchanged:: 1.0
   Added the ``binary`` data type.

.. versionchanged:: 0.9
   If a list of types is given, the key value must match *any* of them.

.. versionchanged:: 0.7.1
   ``dict`` and ``list`` typechecking are now performed with the more generic
   ``Mapping`` and ``Sequence`` types from the builtin ``collections`` module.
   This means that instances of custom types designed to the same interface as
   the builtin ``dict`` and ``list`` types can be validated with Cerberus. We
   exclude strings when type checking for ``list``/``Sequence`` because it
   in the validation situation it is almost certain the string was not the
   intended data type for a sequence.

.. versionchanged:: 0.7
   Added the ``set`` data type.

.. versionchanged:: 0.6
   Added the ``number`` data type.

.. versionchanged:: 0.4.0
   Type validation is always executed first, and blocks other field validation
   rules on failure.

.. versionchanged:: 0.3.0
   Added the ``float`` data type.

.. [#] This is actually an alias of :class:`py2:str` in Python 2.

validator
---------
Validates the value by calling either a function or method.

A function must be implemented like this the following prototype: ::

    def validationname(field, value, error):
        if value is invalid:
            error(field, 'error message')

The ``error`` argument points to the calling validator's ``_error`` method. See
:doc:`customize` on how to submit errors.

Here's an example that tests whether an integer is odd or not:

.. testcode::

    def oddity(field, value, error):
        if not value & 1:
            error(field, "Must be an odd number")

Then, you can validate a value like this:

.. doctest::

    >>> schema = {'amount': {'validator': oddity}}
    >>> v = Validator(schema)
    >>> v.validate({'amount': 10})
    False
    >>> v.errors
    {'amount': ['Must be an odd number']}

    >>> v.validate({'amount': 9})
    True

If the rule's constraint is a string, the :class:`~cerberus.Validator` instance
must have a method with that name prefixed by ``_validator_``. See
:doc:`customize` for an equivalent to the function-based example above.

The constraint can also be a sequence of these that will be called consecutively. ::

   schema = {'field': {'validator': [oddity, 'prime number']}}

.. _valueschema-rule:

valueschema
-----------
Validation schema for all values of a :term:`mapping`.

.. doctest::

    >>> schema = {'numbers': {'type': 'dict', 'valueschema': {'type': 'integer', 'min': 10}}}
    >>> document = {'numbers': {'an integer': 10, 'another integer': 100}}
    >>> v.validate(document, schema)
    True

    >>> document = {'numbers': {'an integer': 9}}
    >>> v.validate(document, schema)
    False

    >>> v.errors
    {'numbers': [{'an integer': ['min value is 10']}]}

.. versionadded:: 0.7
.. versionchanged:: 0.9
   renamed ``keyschema`` to ``valueschema``
