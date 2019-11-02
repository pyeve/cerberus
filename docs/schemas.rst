Validation Schemas
==================

A validation schema is a :term:`mapping`, usually passed as a :class:`dict`.
Schema keys are the keys allowed in the target dictionary. Schema values
express the rules that must be matched by the corresponding target values.

.. testcode::

    schema = {'name': {'type': 'string', 'maxlength': 10}}

In the example above we define a schema with only one key, ``name``, which is
expected to be a string not longer than 10 characters. Something like
``{'name': 'john doe'}`` would validate, while something like ``{'name': 'a
very long string'}`` or ``{'name': 99}`` would not.

By default all keys in a document are optional unless the :ref:`required`-rule
is set ``True`` for individual fields or the validator's :attr:~cerberus.Validator.require_all
is set to ``True`` in order to expect all schema-defined fields to be present in the document.


Registries
----------

There are two default registries in the cerberus module namespace where you can
store definitions for schemas and rules sets which then can be referenced in a
validation schema. You can furthermore instantiate more
:class:`~cerberus.base.RulesSetRegistry` and
:class:`~cerberus.base.SchemaSetRegistry` objects and bind them to the
:attr:`~cerberus.Validator.rules_set_registry` respectively
:attr:`~cerberus.Validator.schema_registry` of a validator. You may also set
these as keyword-arguments upon initialisation.

Using registries is particularly interesting if

  - schemas shall include references to themselves, vulgo: schema recursion
  - schemas contain a lot of reused parts and are supposed to be
    :ref:`serialized <schema-serialization>`


.. doctest::

    >>> from cerberus import schema_registry
    >>> schema_registry.add('non-system user',
    ...                     {'uid': {'min': 1000, 'max': 0xffff}})
    >>> schema = {'sender': {'schema': 'non-system user',
    ...                      'allow_unknown': True},
    ...           'receiver': {'schema': 'non-system user',
    ...                        'allow_unknown': True}}

.. doctest::

    >>> from cerberus import rules_set_registry
    >>> rules_set_registry.extend(
    ...     (('boolean', {'type': 'boolean'}),
    ...     ('booleans', {'valuesrules': 'boolean'}))
    ... )
    >>> schema = {'foo': 'booleans'}


Validation
----------

Validation schemas themselves are validated by default when passed to the
validator or a new set of rules is set for a top-level field. A
:exc:`~cerberus.SchemaError` is raised when an invalid validation schema is
encountered. See :ref:`schema-validation-schema` for a reference.

However, be aware that no validation can be triggered for all changes below
that level or when a used definition in a registry changes. You could therefore
trigger a validation and catch the exception:

    >>> v = Validator({'foo': {'allowed': []}})
    >>> v.schema['foo'] = {'allowed': 1}
    Traceback (most recent call last):
      File "<input>", line 1, in <module>
      File "cerberus/schema.py", line 99, in __setitem__
        self.validate({key: value})
      File "cerberus/schema.py", line 126, in validate
        self._validate(schema)
      File "cerberus/schema.py", line 141, in _validate
        raise SchemaError(self.schema_validator.errors)
    SchemaError: {'foo': {'allowed': 'must be of container type'}}
    >>> v.schema['foo']['allowed'] = 'strings are no valid constraint for allowed'
    >>> v.schema.validate()
    Traceback (most recent call last):
      File "<input>", line 1, in <module>
      File "cerberus/schema.py", line 126, in validate
        self._validate(schema)
      File "cerberus/schema.py", line 141, in _validate
        raise SchemaError(self.schema_validator.errors)
    SchemaError: {'foo': {'allowed': 'must be of container type'}}

Schema validation can be disabled by using the
:class:`~cerberus.UnconcernedValidator` or getting a validator class from
:func:`~cerberus.validator_factory` with the argument ``validated_schema``
set to ``False``. This can useful in an application's production environment to
reduce startup time.


.. _schema-serialization:

Serialization
-------------

Cerberus schemas are built with vanilla Python types: ``dict``, ``list``,
``string``, etc. Even user-defined validation rules are invoked in the schema
by name as a string. A useful side effect of this design is that schemas can
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
    {'age': ['min value is 10']}

You don't have to use YAML of course, you can use your favorite serializer.
:mod:`json` for example. As long as there is a decoder that can produce a nested
``dict``, you can use it to define a schema.

For populating and dumping one of the registries, use
:meth:`~cerberus.Registry.extend` and :meth:`~cerberus.Registry.all`.

.. _PyYAML: http://pyyaml.org
