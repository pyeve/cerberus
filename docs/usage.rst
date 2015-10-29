Cerberus Usage
==============

Basic Usage
-----------
You define a validation schema and pass it to an instance of the
:class:`~cerberus.Validator` class:

.. doctest::

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

Then you simply invoke the :meth:`~cerberus.Validator.validate` to validate
a dictionary against the schema. If validation succeeds, ``True`` is returned:

.. testsetup::

    schema = {'name': {'type': 'string'}}
    v = Validator(schema)
    document = {'name': 'john doe'}

.. doctest::

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True

Alternatively, you can pass both the dictionary and the schema to the
:meth:`~cerberus.Validator.validate` method:

.. doctest::

    >>> v = Validator()
    >>> v.validate(document, schema)
    True

Which can be handy if your schema is changing through the life of the
instance.

Unlike other validation tools, Cerberus will not halt and raise an exception on
the first validation issue. The whole document will always be processed, and
``False`` will be returned if validation failed.  You can then access the
:py:attr:`~cerberus.Validator.errors` property to obtain a list of issues. See
:doc:`Errors & Error Handling <errors>` for different output options.

.. doctest::

    >>> schema = {'name': {'type': 'string'}, 'age': {'type': 'integer', 'min': 10}}
    >>> document = {'name': 'Little Joe', 'age': 5}
    >>> v.validate(document, schema)
    False
    >>> v.errors
    {'age': 'min value is 10'}

You will still get :exc:`~cerberus.SchemaError` and
:exc:`~cerberus.DocumentError` exceptions.

.. versionchanged:: 0.4.1
    The Validator class is callable, allowing for the following shorthand
    syntax:

.. doctest::

    >>> document = {'name': 'john doe'}
    >>> v(document)
    True


Validation Schema
-----------------
A validation schema is a dictionary. Schema keys are the keys allowed in
the target dictionary. Schema values express the rules that must be  matched by
the corresponding target values.

.. testcode::

    schema = {'name': {'type': 'string', 'maxlength': 10}}

In the example above we define a target dictionary with only one key, ``name``,
which is expected to be a string not longer than 10 characters. Something like
``{'name': 'john doe'}`` would validate, while something like ``{'name': 'a
very long string'}`` or ``{'name': 99}`` would not.

By definition all keys are optional unless the :ref:`required`-rule is set for
a key.

See :doc:`validation-rules` and :doc:`normalization-rules` for an extensive
documentation of all supported rules.

.. _allowing-the-unknown:

Allowing the Unknown
--------------------
By default only keys defined in the schema are allowed:

.. doctest::

    >>> schema = {'name': {'type': 'string', 'maxlength': 10}}
    >>> v.validate({'name': 'john', 'sex': 'M'}, schema)
    False
    >>> v.errors
    {'sex': 'unknown field'}

However, you can allow unknown key/value pairs by either setting
``allow_unknown`` to ``True``:

.. doctest::

    >>> v.schema = {}
    >>> v.allow_unknown = True
    >>> v.validate({'name': 'john', 'sex': 'M'})
    True

Or you can set ``allow_unknown`` to a validation schema, in which case
unknown fields will be validated against it:

.. doctest::

    >>> v.schema = {}
    >>> v.allow_unknown = {'type': 'string'}
    >>> v.validate({'an_unknown_field': 'john'})
    True
    >>> v.validate({'an_unknown_field': 1})
    False
    >>> v.errors
    {'an_unknown_field': 'must be of string type'}

``allow_unknown`` can also be set at initialization:

.. doctest::

    >>> v = Validator({}, allow_unknown=True)
    >>> v.validate({'name': 'john', 'sex': 'M'})
    True
    >>> v.allow_unknown = False
    >>> v.validate({'name': 'john', 'sex': 'M'})
    False

``allow_unknown`` can also be set as rule to configure a validator for a nested
mapping that is checked against the :ref:`schema <schema_dict-rule>` rule:

.. doctest::

    >>> v = Validator()
    >>> v.allow_unknown
    False

    >>> schema = {
    ...   'name': {'type': 'string'},
    ...   'a_dict': {
    ...     'type': 'dict',
    ...     'allow_unknown': True,  # this overrides the behaviour for
    ...     'schema': {             # the validation of this definition
    ...       'address': {'type': 'string'}
    ...     }
    ...   }
    ... }

    >>> v.validate({'name': 'john', 'a_dict':{'an_unknown_field': 'is allowed'}}, schema)
    True

    >>> # this fails as allow_unknown is still False for the parent document.
    >>> v.validate({'name': 'john', 'an_unknown_field': 'is not allowed', 'a_dict':{'an_unknown_field': 'is allowed'}}, schema)
    False

    >>> v.errors
    {'an_unknown_field': 'unknown field'}

.. versionchanged:: 0.9
   ``allow_unknown`` can also be set for nested dict fields.

.. versionchanged:: 0.8
   ``allow_unknown`` can also be set to a validation schema.


Fetching Processed Documents
----------------------------

Beside the ``document``-property a ``Validator``-instance has shorthand methods
to process a document and fetch its processed result.

`validated` Method
~~~~~~~~~~~~~~~~~~
There's a wrapper-method :meth:`~cerberus.Validator.validated` that returns the
validated document. If the document didn't validate ``None`` is returned. It
can be useful for flows like this:

.. testsetup::

    documents = ()

.. testcode::

    v = Validator(schema)
    valid_documents = [x for x in [v.validated(y) for y in documents] if x is not None]

If a coercion callable raises a :exc:`TypeError` or :exc:`ValueError` then the
exception will be caught and the validation with fail.  All other exception
pass through.

.. versionadded:: 0.9

`normalized` Method
~~~~~~~~~~~~~~~~~~~
Similary, the :meth:`~cerberus.Validator.normalized` method returns a
normalized copy of a document without validating it:

.. doctest::

    >>> schema = {'amount': {'coerce': int}}
    >>> document = {'model': 'consumerism', 'amount': '1'}
    >>> normalized_document = v.normalized(document, schema)
    >>> type(normalized_document['amount'])
    <type 'int'>

.. versionadded:: 0.10


Schema Definition Formats
-------------------------

Cerberus schemas are built with vanilla Python types: ``dict``, ``list``,
``string``, etc. Even user-defined validation rules are invoked in the schema
by name, as a string. A useful side effect of this design is that schemas can
be defined in a number of ways, for example with PyYAML_.

.. doctest::

    >>> import yaml
    >>> schema_text = '''
    ... name:
    ...   type: string
    ... age:
    ...   type: integer
    ...   min: 10
    ... '''
    >>> schema = yaml.load(schema_text)
    >>> document = {'name': 'Little Joe', 'age': 5}
    >>> v.validate(document, schema)
    False
    >>> v.errors
    {'age': 'min value is 10'}

You don't have to use YAML of course, you can use your favorite serializer.
JSON for example. As long as there is a decoder that can produce a nested
``dict``, you can use it to define a schema.


.. _PyYAML: http://pyyaml.org
