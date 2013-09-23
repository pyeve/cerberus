"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2013 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/
"""

import sys
from datetime import datetime
from . import errors

if sys.version_info[0] == 3:
    _str_type = str
    _int_types = (int,)
else:
    _str_type = basestring
    _int_types = (int, long)


class ValidationError(ValueError):
    """ Raised when the target dictionary is missing or has the wrong format
    """
    pass


class SchemaError(ValueError):
    """ Raised when the validation schema is missing, has the wrong format or
    contains errors.
    """
    pass


class Validator(object):
    """ Validator class. Validates any Python dict against a validation schema,
    which is provided as an argument at class instantiation, or upon calling
    the :func:`validate` method.

    :param schema: optional validation schema.
    :param transparent_schema_rules: if ``True`` unknown schema rules will be
                                 ignored (no SchemaError will be raised).
                                 Defaults to ``False``. Useful you need to
                                 extend the schema grammar beyond Cerberus'
                                 domain.
    :param ignore_none_values: If ``True`` it will ignore None values for type
                               checking. (no UnknowType error will be added).
                               Defaults to ``False``. Useful if your document
                               is composed from function kwargs with defaults.
    :param allow_unknown: if ``True`` unknown key/value pairs (not present in
                          the schema) will be ignored, and validation will
                          pass. Defaults to ``False``, returning an 'unknown
                          field error' un validation.

    .. versionchanged:: 0.4.0
       :func:`validate_update` is deprecated. Use :func:`validate` with
       ``update=True`` instead.
       Type validation is always performed first (only exception being
       ``nullable``). On failure, it blocks other rules on the same field.
       Closes #18.

    .. versionadded:: 0.2.0
       `self.errors` returns an empty list when validate() has not been called.
       Option so allow nullable field values.
       Option to allow unknown key/value pairs.

    .. versionadded:: 0.1.0
       Option to ignore None values for type checking.

    .. versionadded:: 0.0.3
       Support for transparent schema rules.
       Added new 'empty' rule for string fields.

    .. versionadded:: 0.0.2
        Support for addition and validation of custom data types.
    """

    def __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False):
        self.schema = schema
        self.transparent_schema_rules = transparent_schema_rules
        self.ignore_none_values = ignore_none_values
        self.allow_unknown = allow_unknown
        self._errors = []

    @property
    def errors(self):
        """
        :rtype: a list of validation errors. Will be empty if no errors
                were found during. Resets after each call to :func:`validate`.
        """
        return self._errors

    def validate_update(self, document, schema=None):
        """ Validates a Python dicitionary against a validation schema. The
        difference with :func:`validate` is that the ``required`` rule will be
        ignored here.

        :param schema: optional validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantation.
        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors` property for a list of validation errors.

        .. deprecated:: 0.4.0
           Use :func:`validate` with ``update=True`` instead.
        """
        return self._validate(document, schema, update=True)

    def validate(self, document, schema=None, update=False):
        """ Validates a Python dictionary against a validation schema.

        :param document: the dict to validate.
        :param schema: the validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantation.
        :param update: If ``True`` validation of required fields won't be
                       performed.

        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors` property for a list of validation errors.

        .. versionchanged:: 0.4.0
           Support for update mode.
        """
        return self._validate(document, schema, update=update)

    def _validate(self, document, schema=None, update=False):

        self._errors = []
        self.update = update

        if schema is not None:
            self.schema = schema
        elif self.schema is None:
            raise SchemaError(errors.ERROR_SCHEMA_MISSING)
        if not isinstance(self.schema, dict):
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT % str(self.schema))

        if document is None:
            raise ValidationError(errors.ERROR_DOCUMENT_MISSING)
        if not isinstance(document, dict):
            raise ValidationError(errors.ERROR_DOCUMENT_FORMAT % str(document))
        self.document = document

        special_rules = ["required", "nullable", "type"]
        for field, value in self.document.items():

            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition:
                if isinstance(definition, dict):

                    if definition.get("nullable", False) == True \
                       and value is None:  # noqa
                        continue

                    if 'type' in definition:
                        self._validate_type(definition['type'], field, value)
                        if self.errors:
                            continue

                    definition_rules = [rule for rule in definition.keys()
                                        if rule not in special_rules]
                    for rule in definition_rules:
                        validatorname = "_validate_" + rule.replace(" ", "_")
                        validator = getattr(self, validatorname, None)
                        if validator:
                            validator(definition[rule], field, value)
                        elif not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE %
                                              (rule, field))
                else:
                    raise SchemaError(errors.ERROR_DEFINITION_FORMAT % field)

            else:
                if not self.allow_unknown:
                    self._error(errors.ERROR_UNKNOWN_FIELD % field)

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
        missing = set(required) - set(key for key in self.document.keys()
                                      if self.document.get(key) is not None
                                      or not self.ignore_none_values)
        if len(missing):
            self._error(errors.ERROR_REQUIRED_FIELD % ', '.join(missing))

    def _validate_readonly(self, read_only, field, value):
        if read_only:
            self._error(errors.ERROR_READONLY_FIELD % field)

    def _validate_type(self, data_type, field, value):
        validator = getattr(self, "_validate_type_" + data_type, None)
        if validator:
            validator(field, value)
        else:
            raise SchemaError(errors.ERROR_UNKNOWN_TYPE % (data_type, field))

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(errors.ERROR_BAD_TYPE % (field, "string"))

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(errors.ERROR_BAD_TYPE % (field, "integer"))

    def _validate_type_float(self, field, value):
        if not isinstance(value, float):
            self._error(errors.ERROR_BAD_TYPE % (field, "float"))

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(errors.ERROR_BAD_TYPE % (field, "boolean"))

    #def _validate_type_array(self, field, value):
    #    if not isinstance(value, list):
    #        self._error(errors.ERROR_BAD_TYPE % (field, "array (list)"))

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(errors.ERROR_BAD_TYPE % (field, "datetime"))

    def _validate_type_dict(self, field, value):
        if not isinstance(value, dict):
            self._error(errors.ERROR_BAD_TYPE % (field, "dict"))

    def _validate_type_list(self, field, value):
        if not isinstance(value, list):
            self._error(errors.ERROR_BAD_TYPE % (field, "list"))

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, (_str_type, list)):
            if len(value) > max_length:
                self._error(errors.ERROR_MAX_LENGTH % (field, max_length))

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, (_str_type, list)):
            if len(value) < min_length:
                self._error(errors.ERROR_MIN_LENGTH % (field, min_length))

    def _validate_max(self, max_value, field, value):
        if isinstance(value, _int_types):
            if value > max_value:
                self._error(errors.ERROR_MAX_VALUE % (field, max_value))

    def _validate_min(self, min_value, field, value):
        if isinstance(value, _int_types):
            if value < min_value:
                self._error(errors.ERROR_MIN_VALUE % (field, min_value))

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(errors.ERROR_UNALLOWED_VALUE % (value, field))
        elif isinstance(value, list):
            disallowed = set(value) - set(allowed_values)
            if disallowed:
                self._error(
                    errors.ERROR_UNALLOWED_VALUES % (list(disallowed), field)
                )

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(errors.ERROR_EMPTY_NOT_ALLOWED % field)

    def _validate_schema(self, schema, field, value):
        if isinstance(value, list):
            for i in range(len(value)):
                key = "%s[%s]" % (field, str(i))
                validator = self.__class__({key: schema})
                if not validator.validate({key: value[i]}):
                    self._error([error for error in validator.errors])
        elif isinstance(value, dict):
            validator = self.__class__(schema)
            if not validator.validate(value):
                self._error(["'%s': " % field + error
                            for error in validator.errors])
        else:
            self._error(errors.ERROR_BAD_TYPE % (field, "dict"))

    def _validate_items(self, items, field, value):
        if isinstance(items, dict):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, list):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, schema, field, values):
        if len(schema) != len(values):
            self._error(errors.ERROR_ITEMS_LIST % (field, len(schema)))
        else:
            for i in range(len(schema)):
                key = "%s[%s]" % (field, str(i))
                validator = self.__class__({key: schema[i]})
                if not validator.validate({key: values[i]}):
                    self._error([error for error in validator.errors])

    def _validate_items_schema(self, schema, field, value):
        validator = self.__class__(schema)
        for item in value:
            if not validator.validate(item):
                self._error(["'%s': " % field + error
                            for error in validator.errors])
