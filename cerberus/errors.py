"""
This module contains the error messages issued by the Cerberus Validator.
The test suite uses this module as well.
"""

ERROR_BAD_TYPE = "must be of {0} type"
ERROR_COERCION_FAILED = "field '{0}' could not be coerced"
ERROR_DEPENDENCIES_FIELD = "field '{0}' is required"
ERROR_DEPENDENCIES_FIELD_VALUE = \
    "field '{0}' is required with one of these values: {1}"
ERROR_DOCUMENT_FORMAT = "'{0}' is not a document, must be a dict"
ERROR_DOCUMENT_MISSING = "document is missing"
ERROR_EMPTY_NOT_ALLOWED = "empty values not allowed"
ERROR_ITEMS_LIST = "length of list should be {0}"
ERROR_MAX_LENGTH = "max length is {0}"
ERROR_MIN_LENGTH = "min length is {0}"
ERROR_MAX_VALUE = "max value is {0}"
ERROR_MIN_VALUE = "min value is {0}"
ERROR_NOT_NULLABLE = "null value not allowed"
ERROR_READONLY_FIELD = "field is read-only"
ERROR_REGEX = "value does not match regex '{0}'"
ERROR_REQUIRED_FIELD = "required field"
ERROR_UNALLOWED_VALUE = "unallowed value {0}"
ERROR_UNALLOWED_VALUES = "unallowed values {0}"
ERROR_UNKNOWN_FIELD = "unknown field"
ERROR_UNKNOWN_TYPE = "unrecognized data-type '{0}'"

SCHEMA_ERROR_BAD_ALLOW_UNKNOWN = \
    "allow_unknown-definition for {0} must be a bool or a dict"
SCHEMA_ERROR_BAD_DEPENDENCY = \
    "dependency-definition for {0} must be a dict or a list"
SCHEMA_ERROR_CONSTRAINT_TYPE = "the constraint for '{0}' must be a dict"
SCHEMA_ERROR_DEFINITION_CALLABLE = \
    "coerce- and validator-definitions must be a callable"
SCHEMA_ERROR_DEFINITION_FORMAT = \
    "schema definition for field '{0}', must be a dict"
SCHEMA_ERROR_INVALID_DEPENDENCY = "{0} is no valid dependency for {1}"
SCHEMA_ERROR_MISSING = "validation schema missing"
SCHEMA_ERROR_TYPE = "type of field '{0}' must be either 'list' or 'dict'"
SCHEMA_ERROR_UNKNOWN_RULE = "unknown rule '{0}' for field '{0}'"
