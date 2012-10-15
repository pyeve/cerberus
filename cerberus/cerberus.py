'''

This module implements Cerberus Validator class

'''

import sys
from errors import *
from datetime import datetime

if sys.version_info[0] == 3:
    _str_type = str
    _int_types = (int,)
else:
    _str_type = basestring
    _int_types = (int, long)


class ValidationError(ValueError):
    '''Raised when the target dictionary is missing or has the wrong format
    '''
    pass


class SchemaError(ValueError):
    '''Raised when the validation schema is missing, has the wrong format or
    contains errors.
    '''
    pass


class Validator(object):
    ''' Validator class. Validates any Python dict
    against a validation schema, which is provided as an argument at
    class instantiation, or upon calling the :func:`validate` or
    :func:`validate_update` methods.

    :param schema: optional validation schema.
    '''

    def __init__(self, schema=None):
        self.schema = schema

    @property
    def errors(self):
        '''
        :rtype: a list of validation errors. Will be empty if no errors
                were found during. Resets after each call to :func:`validate` or
                :func:`validate_update`.
        '''
        return self._errors

    def validate_update(self, document, schema=None):
        ''' Validates a Python dicitionary against a validation schema. The
        difference with :func:`validate` is that the ``required`` rule will be
        ignored here.

        :param schema: optional validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantation.
        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors` property for a list of validation errors.
        '''
        return self._validate(document, schema, update=True)

    def validate(self, document, schema=None):
        ''' Validates a Python dictionary against a validation schema.

        :param document: the dict to validate.
        :param schema: the validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantation.

        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors` property for a list of validation errors.
        '''
        return self._validate(document, schema, update=False)

    def _validate(self, document, schema=None, update=False):

        self._errors = list()
        self.update = update

        if schema is not None:
            self.schema = schema
        elif self.schema is None:
            raise SchemaError(ERROR_SCHEMA_MISSING)
        if not isinstance(self.schema, dict):
            raise SchemaError(ERROR_SCHEMA_FORMAT % str(self.schema))

        if document is None:
            raise ValidationError(ERROR_DOCUMENT_MISSING)
        if not isinstance(document, dict):
            raise ValidationError(ERROR_DOCUMENT_FORMAT % str(document))
        self.document = document

        special_rules = ["required"]
        for field, value in self.document.items():

            definition = self.schema.get(field)
            if definition:
                if isinstance(definition, dict):
                    definition_rules = [rule for rule in definition.keys()
                                        if rule not in special_rules]
                    for rule in definition_rules:
                        validatorname = "_validate_" + rule.replace(" ", "_")
                        validator = getattr(self, validatorname, None)
                        if validator:
                            validator(definition[rule], field, value)
                        else:
                            raise SchemaError(ERROR_UNKNOWN_RULE %
                                              (rule, field))
                else:
                    raise SchemaError(ERROR_DEFINITION_FORMAT % field)

            else:
                self._error(ERROR_UNKNOWN_FIELD % field)

        if not self.update:
            self._validate_required_fields()

        return len(self._errors) == 0

    def _error(self, _error):
        if isinstance(_error, _str_type):
            self._errors.append(_error)
        else:
            self._errors.extend(_error)

    def _validate_required_fields(self):
        required = list(field for field, definition in self.schema.items()
                        if definition.get('required') is True)
        missing = set(required) - set(self.document.keys())
        if len(missing):
            self._error(ERROR_REQUIRED_FIELD % ', '.join(missing))

    def _validate_readonly(self, read_only, field, value):
        if read_only:
            self._error(ERROR_READONLY_FIELD % field)

    def _validate_type(self, data_type, field, value):
        validator = getattr(self, "_validate_type_" + data_type, None)
        if validator:
            validator(field, value)
        else:
            raise SchemaError(ERROR_UNKNOWN_TYPE % (data_type, field))

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(ERROR_BAD_TYPE % (field, "string"))

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(ERROR_BAD_TYPE % (field, "integer"))

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(ERROR_BAD_TYPE % (field, "boolean"))

    #def _validate_type_array(self, field, value):
    #    if not isinstance(value, list):
    #        self._error(ERROR_BAD_TYPE % (field, "array (list)"))

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(ERROR_BAD_TYPE % (field, "datetime"))

    def _validate_type_dict(self, field, value):
        if not isinstance(value, dict):
            self._error(ERROR_BAD_TYPE % (field, "dict"))

    def _validate_type_list(self, field, value):
        if not isinstance(value, list):
            self._error(ERROR_BAD_TYPE % (field, "list"))

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, _str_type):
            if len(value) > max_length:
                self._error(ERROR_MAX_LENGTH % (field, max_length))

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, _str_type):
            if len(value) < min_length:
                self._error(ERROR_MIN_LENGTH % (field, min_length))

    def _validate_max(self, max_value, field, value):
        if isinstance(value, _int_types):
            if value > max_value:
                self._error(ERROR_MAX_VALUE % (field, max_value))

    def _validate_min(self, min_value, field, value):
        if isinstance(value, _int_types):
            if value < min_value:
                self._error(ERROR_MIN_VALUE % (field, min_value))

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, list):
            disallowed = set(value) - set(allowed_values)
            if disallowed:
                self._error(ERROR_UNALLOWED_VALUES % (list(disallowed), field))

    def _validate_schema(self, schema, field, value):
        if isinstance(value, dict):
            validator = Validator(schema)
            if not validator.validate(value):
                self._error(["'%s': " % field + error
                            for error in validator.errors])
        else:
            self._error(ERROR_BAD_TYPE % (field, "dict"))

    def _validate_items(self, items, field, value):
        if isinstance(items, dict):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, list):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, schemas, field, values):
        if len(schemas) != len(values):
            self._error(ERROR_ITEMS_LIST % (field, len(schemas)))
        else:
            for i in range(len(schemas)):
                key = "_data" + str(i)
                validator = Validator({key: schemas[i]})
                if not validator.validate({key: values[i]}):
                    self._error(["'%s': " % field + error
                                for error in validator.errors])

    def _validate_items_schema(self, schema, field, value):
        validator = Validator(schema)
        for item in value:
            if not validator.validate(item):
                self._error(["'%s': " % field + error
                            for error in validator.errors])
