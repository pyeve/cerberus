Extending Cerberus
==================

Cerberus supports custom validation in two styles:

    * `Class-based Custom Validators`_
    * `Function-based Custom Validation`_

As a general rule, when you are customizing validators in your application,
``Class-based`` style is more suitable for common validators, which are
also more human-readable (since the rule name is defined by yourself), while
``Function-based`` style is more suitable for special and one-off ones.


Class-based Custom Validators
-----------------------------
Suppose that in our use case some values can only be expressed as odd integers,
therefore we decide to add support for a new ``isodd`` rule to our validation
schema:

.. testcode::

    schema = {'oddity': {'isodd': True, 'type': 'integer'}}

This is how we would go to implement that:

.. testcode::

    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_isodd(self, isodd, field, value):
            if isodd and not bool(value & 1):
                self._error(field, "Must be an odd number")

By subclassing Cerberus :class:`~cerberus.Validator` class and adding the custom
``_validate_<rulename>`` function, we just enhanced Cerberus to suit our needs.
The custom rule ``isodd`` is now available in our schema and, what really
matters, we can use it to validate all odd values:

.. doctest::

    >>> v = MyValidator(schema)
    >>> v.validate({'oddity': 10})
    False
    >>> v.errors
    {'oddity': 'Must be an odd number'}
    >>> v.validate({'oddity': 9})
    True

In a schema schema you can use space characters instead of underscores, e.g.
``{'oddity': {'is odd': 42'}}`` is an alias for ``{'oddity': {'is_odd': 42'}}``.


To make use of additional contextual information in a sub-class of
:class:`~cerberus.Validator`, use a pattern like this:

.. testcode::

    class MyValidator(Validator):
        def __init__(self, *args, **kwargs):
            if 'additional_context' in kwargs:
                self.additional_context = kwargs['additional_context']
            super(MyValidator, self).__init__(*args, **kwargs)

        def _validate_type_foo(self, field, value):
            make_use_of(self.additional_context)

.. versionadded:: 0.9

.. _new-types:

Custom Data Types
~~~~~~~~~~~~~~~~~
Cerberus supports and validates several standard data types (see :ref:`type`).
When building a `Class-based Custom Validators`_ you can add and validate your
own data types.
For example `Eve <http://python-eve.org>`_ (a tool for quickly building and
deploying RESTful Web Services) supports a custom ``objectid`` type, which is
used to validate that field values conform to the BSON/MongoDB ``ObjectId``
format.

You extend the supported set of data types by adding
a ``_validate_type_<typename>`` method to your own :class:`~cerberus.Validator`
subclass. This snippet, directly from Eve source, shows how the ``objectid``
has been implemented:

.. testcode::

     def _validate_type_objectid(self, field, value):
         """ Enables validation for `objectid` schema attribute.

         :param field: field name.
         :param value: field value.
         """
         if not re.match('[a-f0-9]{24}', value):
             self._error(field, ERROR_BAD_TYPE.format('ObjectId'))

.. versionadded:: 0.0.2


Function-based Custom Validation
--------------------------------
With a special rule ``validator``, you can customize validators by defining
your own functions with the following prototype: ::

    def validate_<fieldname>(field, value, error):
        pass

As a contrast, if the odd value is a special case, you may want to make the
above rule ``isodd`` into ``Function-based`` style, which is a more lightweight
alternative:

.. testcode::

    def validate_oddity(field, value, error):
        if not bool(value & 1):
            error(field, "Must be an odd number")

Then, you can validate an odd value like this:

.. doctest::

    >>> schema = {'oddity': {'validator': validate_oddity}}
    >>> v = Validator(schema)
    >>> v.validate({'oddity': 10})
    False
    >>> v.errors
    {'oddity': 'Must be an odd number'}

    >>> v.validate({'oddity': 9})
    True

.. versionadded:: 0.8


Limitations
-----------
You must not call your custom rule ``validator`` and it may be a bad idea to
overwrite particular contributed rules.


Relevant `Validator`-attributes
-------------------------------

There are some attributes of a :class:`~cerberus.Validator` that you should be
aware of when writing `Class-based Custom Validators`_.

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
later point, you need to call :meth:`~cerberus._error` with two mandatory
arguments:

  - the field where the error occurred
  - an instance of a :class:`~cerberus.errors.ErrorDefinition`

For custom rules you need to define an error as ``ErrorDefinition`` with a
unique id and the causing rule that is violated. See :mod:`~cerberus.errors`
for a list of the contributed error definitions.

Optionally you can submit further arguments as information. Error handlers
that are targeted for humans will use these as positional arguments when
formatting a message with :py:meth:`str.format`. Serializing handlers will keep
these values in a list. Keep in mind that bit 7 marks a group error.

.. versionadded:: 0.10

Simple custom errors
....................
A simpler form is to call :meth:`~cerberus._error` with the field and a string
as message. However the resulting error will contain no information about the
violated constraint. This is supposed to maintain backward compatibility, but
can also be used when an in-depth error handling isn't needed.

Multiple errors
...............
When using child-validators, it is a convenience to submit all their errors
(:attr:`~cerberus.Validator._errors`); which is a list of
:class:`~cerberus.errors.ValidationError` instances.

.. versionadded:: 0.10

`Validator.__get_child_validator`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need another instance of your :class:`~cerberus.Validator`-subclass, the
:meth:`~cerberus.Validator.__get_child_validator`-method returns another
instance that is initiated with the same arguments as ``self`` was. You can
specify overriding keyword-arguments.
As the properties ``document_path`` and ``schema_path`` (see below) are
inherited by the child validator, you can extend these by passing a single
value or values-tuple with the keywords ``document_crumb`` and
``schema_crumb``.
Study the source code for example usages.

.. versionadded:: 0.9

.. versionchanged:: 0.10
    Added ``document_crumb`` and ``schema_crumb`` as optional keyword-
    arguments.

`Validator.root_document` & `Validator.root_schema`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A child-validator - as used when validating a ``schema`` - can access the first
generation validator's document and schema that are being processed via its
``root_document`` and ``root_schema``-properties.
It's untested what happens when you change that. It may make ``boom``.

.. versionadded:: 0.10

`Validator.document_path` & `Validator.schema_path`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These properties maintain the path of keys within the document respectively the
schema that was traversed by possible parent-validators. Both will be used as
base path when an error is submitted.

.. versionadded:: 0.10
