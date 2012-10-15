'''

This module contains the error messages issued by the Cerberus Validator.
The test suite uses this module as well.

'''
ERROR_SCHEMA_MISSING = "validation schema missing"
ERROR_SCHEMA_FORMAT = "'%s' is not a schema, must be a dict"
ERROR_DOCUMENT_MISSING = "document is missing"
ERROR_DOCUMENT_FORMAT = "'%s' is not a document, must be a dict"
ERROR_UNKNOWN_RULE = "unknown rule '%s' for field '%s'"
ERROR_DEFINITION_FORMAT = "schema definition for field '%s' must be a dict"
ERROR_UNKNOWN_FIELD = "unknown field '%s'"
ERROR_REQUIRED_FIELD = "required field(s) are missing: '%s'"
ERROR_UNKNOWN_TYPE = "unrecognized data-type '%s' for field '%s'"
ERROR_BAD_TYPE = "value of field '%s' must be of %s type"
ERROR_MIN_LENGTH = "min length for field '%s' is %d"
ERROR_MAX_LENGTH = "max length for field '%s' is %d"
ERROR_UNALLOWED_VALUES = "unallowed values %s for field '%s'"
ERROR_ITEMS_LIST = "'%s': lenght of list should be %d"
ERROR_READONLY_FIELD = "field '%s' is read-only"
ERROR_MAX_VALUE = "max value for field '%s' is %d"
ERROR_MIN_VALUE = "min value for field '%s' is %d"
