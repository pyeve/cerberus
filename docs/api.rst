API Documentation
=================

Validator Class
---------------

.. autoclass:: cerberus.Validator
  :members: allow_unknown, clear_caches, document, document_error_tree,
            document_path, _drop_remaining_rules, _error, error_handler,
            _errors, errors, _get_child_validator, ignore_none_values,
            is_child, _lookup_field, mandatory_validations, normalized,
            priority_validations, purge_unknown, recent_error,
            _remaining_rules, root_allow_unknown, root_document, root_schema,
            rules_set_registry, schema, schema_error_tree, schema_path,
            schema_registry, _valid_schemas, validate, validated


Rules Set & Schema Registry
---------------------------

.. autoclass:: cerberus.Registry
  :members:


Error Handlers
--------------

.. autoclass:: cerberus.errors.BaseErrorHandler
  :members:
  :private-members:
  :special-members:

.. autoclass:: cerberus.errors.BasicErrorHandler


Python Error Representations
----------------------------

.. autoclass:: cerberus.errors.ValidationError
  :members:

.. _error-codes:

Error Codes
~~~~~~~~~~~

These errors are used as :attr:`~cerberus.errors.ValidationError.code`.

.. include:: includes/error-codes.rst

.. autoclass:: cerberus.errors.ErrorList

.. autoclass:: cerberus.errors.ErrorTree
  :members:

.. autoclass:: cerberus.errors.DocumentErrorTree

.. autoclass:: cerberus.errors.SchemaErrorTree


Exceptions
----------

.. autoexception:: cerberus.SchemaError

.. autoexception:: cerberus.DocumentError


Utilities
---------

.. automodule:: cerberus.utils
  :members:


.. _schema-validation-schema:

Schema Validation Schema
------------------------

Against this schema validation schemas given to a vanilla
:class:`~cerberus.Validator` will be validated:

.. include:: includes/schema-validation-schema.rst
