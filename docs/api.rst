API Documentation
=================

Validator Class
---------------

.. autoclass:: cerberus.Validator
  :show-inheritance:
  :inherited-members:
  :members: allow_unknown, clear_caches, document, document_error_tree,
            document_path, _drop_remaining_rules, _error, error_handler,
            _errors, errors, _get_child_validator, ignore_none_values,
            is_child, _lookup_field, mandatory_validations, normalized,
            priority_validations, purge_unknown, recent_error,
            require_all, _remaining_rules, root_allow_unknown, root_document,
            root_require_all, root_schema, rules_set_registry, schema,
            schema_error_tree, schema_path, schema_registry, types,
            types_mapping, _valid_schemas, validate, validated


Rules Set & Schema Registry
---------------------------

.. autoclass:: cerberus.base.Registry
   :members:


.. autoclass:: cerberus.schema.RulesSetRegistry
   :show-inheritance:

.. autoclass:: cerberus.schema.SchemaRegistry
   :show-inheritance:


Type Definitions
----------------

.. autoclass:: cerberus.TypeDefinition


Error Handlers
--------------

.. autoclass:: cerberus.errors.BaseErrorHandler
   :members:
   :private-members:
   :special-members:

.. autoclass:: cerberus.errors.BasicErrorHandler
   :show-inheritance:


Python Error Representations
----------------------------

.. autoclass:: cerberus.errors.ErrorDefinition

.. autoclass:: cerberus.errors.ValidationError
   :members:

.. _error-codes:

Error Codes
~~~~~~~~~~~

Its :attr:`code` attribute uniquely identifies an
:class:`~cerberus.errors.ErrorDefinition` that is used a concrete error's
:attr:`~cerberus.errors.ValidationError.code`.
Some codes are actually reserved to mark a shared property of different errors.
These are useful as bitmasks while processing errors. This is the list of the
reserved codes:

============= ======== === ===================================================
``0110 0000`` ``0x60``  96 An error that occurred during normalization.
``1000 0000`` ``0x80`` 128 An error that contains child errors.
``1001 0000`` ``0x90`` 144 An error that was emitted by one of the \*of-rules.
============= ======== === ===================================================

None of these bits in the upper nibble must be used to enumerate error
definitions, but only to mark one with the associated property.

.. important::

    Users are advised to set bit 8 for self-defined errors. So the code
    ``0001 0000 0001`` / ``0x101`` would the first in a domain-specific set of
    error definitions.


This is a list of all error defintions that are shipped with the
:mod:`~cerberus.errors` module:

.. include:: includes/error-codes.rst

Error Containers
~~~~~~~~~~~~~~~~

.. autoclass:: cerberus.errors.ErrorList

.. autoclass:: cerberus.errors.ErrorTree
   :members:

.. autoclass:: cerberus.errors.DocumentErrorTree
   :show-inheritance:

.. autoclass:: cerberus.errors.SchemaErrorTree
   :show-inheritance:


Exceptions
----------

.. autoexception:: cerberus.SchemaError

.. autoexception:: cerberus.DocumentError


Utilities
---------

.. autofunction:: cerberus.validator_factory


.. _schema-validation-schema:

Schema Validation Schema
------------------------

Against this schema validation schemas given to a vanilla
:class:`~cerberus.Validator` will be validated:

.. include:: includes/schema-validation-schema.rst
