Extending Cerberus
==================

Custom Validators
-----------------
Cerberus supports custom validation in two styles:

    * :ref:`class_validator`
    * :ref:`function_validator`

As a general rule, when you are customizing validators in your application,
``Class-based`` style is more suitable for common validators, which are
also more human-readable (since the rule name is defined by yourself), while
``Function-based`` style is more suitable for special and one-off ones.

.. _class_validator:

Class-based Custom Validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

.. versionadded:: 0.7.1
    Custom validators also have access to a special ``self.document`` variable
    that allows validation of a field to happen in context of the rest of the
    document.

To make use of additional contextual information in a sub-class of :class:`~cerberus.Validator`,
use a pattern like this:

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
When building :ref:`class_validator` you can add and validate your own data types.
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

.. _function_validator:

Function-based Custom Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~

You must not call your custom rule ``validator`` and it may be a bad idea to
overwrite particular contributed rules.

Relevant `Validator`-properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Validator.__get_child_validator`
.................................

If you need another instance of your ``Validator``-subclass, the
``__get_child_validator``-method returns another instance that is initiated
with the same arguments as ``self`` was. You can specify overriding keyword-
arguments.

.. versionadded:: 0.9

`Validator.root_document`
.........................

A child-validator - as used when validating a ``schema`` - can access the first
generation validator's document that is being processed via its
``root_document``-property.
It's untested what happens when you change that. It may make ``boom``.

.. versionadded:: 0.10
