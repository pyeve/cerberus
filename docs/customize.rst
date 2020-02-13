Extending Cerberus
==================

Though you can use functions in conjunction with the ``coerce`` and the
``check_with`` rules, you can easily extend the :class:`~cerberus.Validator`
class with custom ``rules``, ``types``, ``check_with`` handlers, ``coercers``
and ``default_setters``.
While the function-based style is more suitable for special and one-off uses,
a custom class leverages these possibilities:

    * custom rules can be defined with constrains in a schema
    * extending the available :ref:`type` s
    * use additional contextual data
    * schemas are serializable

The references in schemas to these custom methods can use space characters
instead of underscores, e.g. ``{'foo': {'check_with': 'is odd'}}`` is an alias
for ``{'foo': {'check_with': 'is_odd'}}``.


Custom Rules
------------
Suppose that in our use case some values can only be expressed as odd integers,
therefore we decide to add support for a new ``is_odd`` rule to our validation
schema:

.. testcode::

    schema = {'amount': {'is odd': True, 'type': 'integer'}}

This is how we would go to implement that:

.. testcode::

    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_is_odd(self, constraint, field, value):
            """ Test the oddity of a value.

            The rule's arguments are validated against this schema:
            {'type': 'boolean'}
            """
            if constraint is True and not bool(value & 1):
                self._error(field, "Must be an odd number")

By subclassing Cerberus :class:`~cerberus.Validator` class and adding the custom
``_validate_<rulename>`` method, we just enhanced Cerberus to suit our needs.
The custom rule ``is_odd`` is now available in our schema and, what really
matters, we can use it to validate all odd values:

.. doctest::

    >>> v = MyValidator(schema)
    >>> v.validate({'amount': 10})
    False
    >>> v.errors
    {'amount': ['Must be an odd number']}
    >>> v.validate({'amount': 9})
    True

As schemas themselves are validated, you can provide constraints as literal
Python expression in the docstring of the rule's implementing method to
validate the arguments given in a schema for that rule. Either the docstring
contains solely the literal or the literal is placed at the bottom of the
docstring preceded by
``The rule's arguments are validated against this schema:``
See the source of the contributed rules for more examples.


.. _new-types:

Custom Data Types
-----------------
Cerberus supports and validates several standard data types (see :ref:`type`).
When building a custom validator you can add and validate your own data types.

Additional types can be added on the fly by assigning a
:class:`~cerberus.TypeDefinition` to the designated type name in
:attr:`~cerberus.Validator.types_mapping`:

.. testcode::

    from decimal import Decimal

    decimal_type = cerberus.TypeDefinition('decimal', (Decimal,), ())

    Validator.types_mapping['decimal'] = decimal_type

.. caution::

    As the ``types_mapping`` property is a mutable type, any change to its
    items on an instance will affect its class.

They can also be defined for subclasses of :class:`~cerberus.Validator`:

.. testcode::

    from decimal import Decimal

    decimal_type = cerberus.TypeDefinition('decimal', (Decimal,), ())

    class MyValidator(Validator):
        types_mapping = Validator.types_mapping.copy()
        types_mapping['decimal'] = decimal_type


.. versionadded:: 0.0.2

.. versionchanged:: 1.0
   The type validation logic changed, see :doc:`upgrading`.

.. versionchanged:: 1.2
   Added the :attr:`~cerberus.Validator.types_mapping` property and marked
   methods for testing types as deprecated.

.. _check-with-rule-methods:

Methods that can be referenced by the check_with rule
-----------------------------------------------------
If a validation test doesn't depend on a specified constraint from a schema or
needs to be more complex than a rule should be, it's possible to rather define
it as *value checker* than as a rule. There are two ways to use the
:ref:`check_with rule <check-with-rule>`.

One is by extending :class:`~cerberus.Validator` with a method prefixed with
``_check_with_``. This allows to access the whole context of the validator
instance including arbitrary configuration values and state. To reference such
method using the ``check_with`` rule, simply pass the unprefixed method name as
a string constraint.

For example, one can define an ``oddity`` validator method as follows:

.. testcode::

    class MyValidator(Validator):
        def _check_with_oddity(self, field, value):
            if not value & 1:
                self._error(field, "Must be an odd number")

Usage would look something like:

.. testcode::

    schema = {'amount': {'type': 'integer', 'check_with': 'oddity'}}

The second option to use the rule is to define a standalone function and pass
it as the constraint. This brings with it the benefit of not having to extend
``Validator``. To read more about this implementation and see examples check
out the rule's documentation.

.. _custom-coercer:

Custom Coercers
---------------
You can also define custom methods that return a ``coerce`` d value or point to
a method as ``rename_handler``. The method name must be prefixed with
``_normalize_coerce_``.

.. testcode::

    class MyNormalizer(Validator):
        def __init__(self, multiplier, *args, **kwargs):
            super(MyNormalizer, self).__init__(*args, **kwargs)
            self.multiplier = multiplier

        def _normalize_coerce_multiply(self, value):
            return value * self.multiplier

.. doctest::

   >>> schema = {'foo': {'coerce': 'multiply'}}
   >>> document = {'foo': 2}
   >>> MyNormalizer(2).normalized(document, schema)
   {'foo': 4}


Custom Default Setters
----------------------
Similar to custom rename handlers, it is also possible to create custom default
setters.

.. testcode::

    from datetime import datetime

    class MyNormalizer(Validator):
        def _normalize_default_setter_utcnow(self, document):
            return datetime.utcnow()

.. doctest::

   >>> schema = {'creation_date': {'type': 'datetime', 'default_setter': 'utcnow'}}
   >>> MyNormalizer().normalized({}, schema)
   {'creation_date': datetime.datetime(...)}


Limitations
-----------
It may be a bad idea to overwrite particular contributed rules.


Attaching Configuration Data And Instantiating Custom Validators
----------------------------------------------------------------
It's possible to pass arbitrary configuration values when instantiating a
:class:`~cerberus.Validator` or a subclass as keyword arguments (whose names
are not used by Cerberus). These can be used in all of the handlers described
in this document that have access to the instance.
Cerberus ensures that this data is available in all child instances that may
get spawned during processing. When you implement an ``__init__`` method on
a customized validator, you must ensure that all positional and keyword
arguments are also passed to the parent class' initialization method. Here's
an example pattern:

.. testcode::

    class MyValidator(Validator):
        def __init__(self, *args, **kwargs):
            # assign a configuration value to an instance property
            # for convenience
            self.additional_context = kwargs.get('additional_context')
            # pass all data to the base classes
            super(MyValidator, self).__init__(*args, **kwargs)

        # alternatively a dynamic property can be defined, rendering
        # the __init__ method unnecessary in this example case
        @property
        def additional_context(self):
            return self._config.get('additional_context', 'bar')

        # an optional property setter if you deal with state
        @additional_context.setter
        def additional_context(self, value):
            self._config["additional_context"] = value

        def _check_with_foo(self, field, value):
            make_use_of(self.additional_context)

.. warning::

    It is neither recommended to access the ``_config`` property in other
    situations than outlined in the sketch above nor to to change its contents
    during the processing of a document. Both cases are not tested and are
    unlikely to get officially supported.

.. versionadded:: 0.9

There's a function :func:`~cerberus.utils.validator_factory` to get a
:class:`Validator` mutant with concatenated docstrings.

.. versionadded:: 1.0


Relevant `Validator`-attributes
-------------------------------
There are some attributes of a :class:`~cerberus.Validator` that you should be
aware of when writing custom Validators.

`Validator.document`
~~~~~~~~~~~~~~~~~~~~

A validator accesses the :attr:`~cerberus.Validator.document` property when
fetching fields for validation. It also allows validation of a field to happen
in context of the rest of the document.

.. versionadded:: 0.7.1

`Validator.schema`
~~~~~~~~~~~~~~~~~~

Alike, the :attr:`~cerberus.Validator.schema` property holds the used schema.

.. note::

    This attribute is not the same object that was passed as ``schema`` to the
    validator at some point. Also, its content may differ, though it still
    represents the initial constraints. It offers the same interface like a
    :class:`dict`.

`Validator._error`
~~~~~~~~~~~~~~~~~~

There are three signatures that are accepted to submit errors to the
``Validator``'s error stash. If necessary the given information will be parsed
into a new instance of :class:`~cerberus.errors.ValidationError`.

Full disclosure
...............
In order to be able to gain complete insight into the context of an error at a
later point, you need to call :meth:`~cerberus.Validator._error` with two
mandatory arguments:

  - the field where the error occurred
  - an instance of a :class:`~cerberus.errors.ErrorDefinition`

For custom rules you need to define an error as ``ErrorDefinition`` with a
unique id and the causing rule that is violated. See :mod:`~cerberus.errors`
for a list of the contributed error definitions. Keep in mind that bit 7 marks
a group error, bit 5 marks an error raised by a validation against different
sets of rules.

Optionally you can submit further arguments as information. Error handlers
that are targeted for humans will use these as positional arguments when
formatting a message with :py:meth:`str.format`. Serializing handlers will keep
these values in a list.

.. versionadded:: 1.0

Simple custom errors
....................
A simpler form is to call :meth:`~cerberus._error` with the field and a string
as message. However the resulting error will contain no information about the
violated constraint. This is supposed to maintain backward compatibility, but
can also be used when an in-depth error handling isn't needed.

Multiple errors
...............
When using child-validators, it is a convenience to submit all their errors
; which is a list of :class:`~cerberus.errors.ValidationError` instances.

.. versionadded:: 1.0

`Validator._get_child_validator`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need another instance of your :class:`~cerberus.Validator`-subclass, the
:meth:`~cerberus.Validator._get_child_validator`-method returns another
instance that is initiated with the same arguments as ``self`` was. You can
specify overriding keyword-arguments.
As the properties ``document_path`` and ``schema_path`` (see below) are
inherited by the child validator, you can extend these by passing a single
value or values-tuple with the keywords ``document_crumb`` and
``schema_crumb``.
Study the source code for example usages.

.. versionadded:: 0.9

.. versionchanged:: 1.0
    Added ``document_crumb`` and ``schema_crumb`` as optional keyword-
    arguments.

`Validator.root_document`, `.root_schema`, `.root_allow_unknown` & `.root_require_all`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A child-validator - as used when validating a ``schema`` - can access the first
generation validator's document and schema that are being processed as well as
the constraints for unknown fields via its ``root_document``, ``root_schema``,
``root_allow_unknown`` and ``root_require_all`` properties.

.. versionadded:: 1.0

.. versionchanged:: 1.3
    Added ``root_require_all``

`Validator.document_path` & `Validator.schema_path`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These properties maintain the path of keys within the document respectively the
schema that was traversed by possible parent-validators. Both will be used as
base path when an error is submitted.

.. versionadded:: 1.0

`Validator.recent_error`
~~~~~~~~~~~~~~~~~~~~~~~~

The last single error that was submitted is accessible through the
``recent_error``-attribute.

.. versionadded:: 1.0

`Validator.mandatory_validations`, `Validator.priority_validations` & `Validator._remaining_rules`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use these class properties and instance instance property if you want
to adjust the validation logic for each field validation.
``mandatory_validations`` is a tuple that contains rules that will be validated
for each field, regardless if the rule is defined for a field in a schema or
not.
``priority_validations`` is a tuple of ordered rules that will be validated
before any other.
``_remaining_rules`` is a list that is populated under consideration of these
and keeps track of the rules that are next in line to be evaluated. Thus it can
be manipulated by rule handlers to change the remaining validation for the
current field.
Preferably you would call :meth:`~cerberus.Validator._drop_remaining_rules`
to remove particular rules or all at once.

.. versionadded:: 1.0

.. versionchanged:: 1.2
    Added ``_remaining_rules`` for extended leverage.
