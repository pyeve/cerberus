"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2014 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/
"""

import sys
import re
import copy
from datetime import datetime
from collections import Mapping, Sequence
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

    .. versionadded: 0.8
      'allow_unknown' can be a schema used to validate unknown fields.
       Support for function-based validation mode.

    .. versionchanged:: 0.7.2
       Successfully validate int as a float type.

    .. versionchanged:: 0.7.1
       Validator options like 'allow_unknown' and 'ignore_none_values' are now
       taken into consideration when validating sub-dictionaries.
       Make self.document always the root level document.
       Up-front validation for schemas.

    .. versionadded:: 0.7
       'keyschema' validation rule.
       'regex' validation rule.
       'dependencies' validation rule.
       'mix', 'max' now apply on floats and numbers too. Closes #30.
       'set' data type.

    .. versionadded:: 0.6
       'number' (integer or float) validator.

    .. versionchanged:: 0.5.0
       ``validator.errors`` returns a dict where keys are document fields and
       values are validation errors.

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
    special_rules = "required", "nullable", "type", "dependencies"

    def __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False):
        self.transparent_schema_rules = transparent_schema_rules
        self.ignore_none_values = ignore_none_values
        self.allow_unknown = allow_unknown
        if schema:
            self.validate_schema(schema)
        self.schema = schema
        self._errors = {}

    def __call__(self, *args, **kwargs):
        return self.validate(*args, **kwargs)

    @property
    def errors(self):
        """
        :rtype: a list of validation errors. Will be empty if no errors
                were found during. Resets after each call to :func:`validate`.
        """
        return self._errors

    def validate_update(self, document, schema=None, context=None):
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
        return self._validate(document, schema, update=True, context=context)

    def validate(self, document, schema=None, update=False, context=None):
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
        return self._validate(document, schema, update=update, context=context)

    def _validate(self, document, schema=None, update=False, context=None):

        self._errors = {}
        self.update = update

        if schema is not None:
            self.validate_schema(schema)
            self.schema = schema
        elif self.schema is None:
            raise SchemaError(errors.ERROR_SCHEMA_MISSING)

        if document is None:
            raise ValidationError(errors.ERROR_DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise ValidationError(errors.ERROR_DOCUMENT_FORMAT % str(document))

        # make root document available for validators (Cerberus #42, Eve #295)
        if context is not None:
            self.document = context
        else:
            self.document = document

        for field, value in document.items():
            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition is not None:
                if value is None:
                    if definition.get("nullable", False) is True:
                        continue
                    else:
                        self._error(field, errors.ERROR_NOT_NULLABLE)

                if 'type' in definition:
                    self._validate_type(definition['type'], field, value)
                    if self.errors.get(field):
                        continue

                if "dependencies" in definition:
                    self._validate_dependencies(
                        document=document,
                        dependencies=definition["dependencies"],
                        field=field
                    )
                    if self.errors.get(field):
                        continue

                definition_rules = [rule for rule in definition.keys()
                                    if rule not in self.special_rules]
                for rule in definition_rules:
                    validatorname = "_validate_" + rule.replace(" ", "_")
                    validator = getattr(self, validatorname, None)
                    if validator:
                        validator(definition[rule], field, value)
            else:
                if self.allow_unknown:
                    if isinstance(self.allow_unknown, Mapping):
                        # validate that unknown fields matches the schema
                        # for unknown_fields
                        unknown_validator = Validator({field:
                                                       self.allow_unknown})
                        if not unknown_validator.validate({field: value}):
                            self._error(field, unknown_validator.errors[field])
                    else:
                        # allow uknown field to pass without any kind of
                        # validation
                        pass
                else:
                    self._error(field, errors.ERROR_UNKNOWN_FIELD)

        if not self.update:
            self._validate_required_fields(document)

        return len(self._errors) == 0

    def _error(self, field, _error):
        field_errors = self._errors.get(field, [])

        if not isinstance(field_errors, list):
            field_errors = [field_errors]

        if isinstance(_error, (_str_type, dict)):
            field_errors.append(_error)
        else:
            field_errors.extend(_error)

        if len(field_errors) == 1:
            field_errors = field_errors.pop()

        self._errors[field] = field_errors

    def validate_schema(self, schema):
        """ Validates a schema against supported rules.

        :param schema: the schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.

        .. versionadded:: 0.7.1
        """

        if not isinstance(schema, Mapping):
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT % str(schema))

        for field, constraints in schema.items():
            if not isinstance(constraints, Mapping):
                raise SchemaError(errors.ERROR_DEFINITION_FORMAT % field)
            for constraint, value in constraints.items():
                if constraint == 'type':
                    if not hasattr(self, '_validate_type_' + value):
                        raise SchemaError(
                            errors.ERROR_UNKNOWN_TYPE % value)
                elif constraint in self.special_rules:
                    pass
                elif constraint == 'schema':
                    if constraints['type'] == 'list':
                        self.validate_schema({'schema': value})
                    else:
                        self.validate_schema(value)
                elif constraint == 'items':
                    if isinstance(value, Mapping):
                        # list of dicts, deprecated
                        self.validate_schema(value)
                    else:
                        for item_schema in value:
                            self.validate_schema({'schema': item_schema})
                elif not hasattr(self, '_validate_' + constraint):
                    if not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE % (
                                constraint, field))

    def _validate_required_fields(self, document):
        """ Validates that required fields are not missing. If dependencies
        are precised then validate 'required' only if all dependencies
        are validated.

        :param document: the document being validated.
        """
        required = list(field for field, definition in self.schema.items()
                        if definition.get('required') is True)
        missing = set(required) - set(key for key in document.keys()
                                      if document.get(key) is not None
                                      or not self.ignore_none_values)

        for field in missing:
            dependencies = self.schema[field].get('dependencies')
            dependencies_validated = self._validate_dependencies(
                document, dependencies, field, break_on_error=True)

            if dependencies_validated:
                self._error(field, errors.ERROR_REQUIRED_FIELD)

    def _validate_readonly(self, read_only, field, value):
        if read_only:
            self._error(field, errors.ERROR_READONLY_FIELD)

    def _validate_regex(self, match, field, value):
        """
        .. versionadded:: 0.7
        """
        pattern = re.compile(match)
        if not pattern.match(value):
            self._error(field, errors.ERROR_REGEX % match)

    def _validate_type(self, data_type, field, value):
        validator = getattr(self, "_validate_type_" + data_type, None)
        validator(field, value)

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE % "string")

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE % "integer")

    def _validate_type_float(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE % "float")

    def _validate_type_number(self, field, value):
        """
        .. versionadded:: 0.6
        """
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE % "number")

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(field, errors.ERROR_BAD_TYPE % "boolean")

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(field, errors.ERROR_BAD_TYPE % "datetime")

    def _validate_type_dict(self, field, value):
        if not isinstance(value, Mapping):
            self._error(field, errors.ERROR_BAD_TYPE % "dict")

    def _validate_type_list(self, field, value):
        if not isinstance(value, Sequence) or isinstance(
                value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE % "list")

    def _validate_type_set(self, field, value):
        if not isinstance(value, set):
            self._error(field, errors.ERROR_BAD_TYPE % "set")

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, Sequence):
            if len(value) > max_length:
                self._error(field, errors.ERROR_MAX_LENGTH % max_length)

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, Sequence):
            if len(value) < min_length:
                self._error(field, errors.ERROR_MIN_LENGTH % min_length)

    def _validate_max(self, max_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value > max_value:
                self._error(field, errors.ERROR_MAX_VALUE % max_value)

    def _validate_min(self, min_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value < min_value:
                self._error(field, errors.ERROR_MIN_VALUE % min_value)

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE % value)
        elif isinstance(value, Sequence):
            disallowed = set(value) - set(allowed_values)
            if disallowed:
                self._error(field,
                            errors.ERROR_UNALLOWED_VALUES % list(disallowed))
        elif isinstance(value, int):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE % value)

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.ERROR_EMPTY_NOT_ALLOWED)

    def _validate_schema(self, schema, field, value):
        if isinstance(value, Sequence):
            list_errors = {}
            for i in range(len(value)):
                validator = self.__class__({i: schema})
                validator.validate({i: value[i]}, context=self.document)
                list_errors.update(validator.errors)
            if len(list_errors):
                self._error(field, list_errors)
        elif isinstance(value, Mapping):
            validator = copy.copy(self)
            validator.schema = schema
            validator.validate(value, context=self.document)
            if len(validator.errors):
                self._error(field, validator.errors)
        else:
            self._error(field, errors.ERROR_BAD_TYPE % "dict or list")

    def _validate_keyschema(self, schema, field, value):
        for key, document in value.items():
            validator = self.__class__()
            validator.validate(
                {key: document}, {key: schema}, context=self.document)
            if len(validator.errors):
                self._error(field, validator.errors)

    def _validate_items(self, items, field, value):
        if isinstance(items, Mapping):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, Sequence):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, schema, field, values):
        if len(schema) != len(values):
            self._error(field, errors.ERROR_ITEMS_LIST % len(schema))
        else:
            for i in range(len(schema)):
                validator = self.__class__({i: schema[i]})
                validator.validate({i: values[i]}, context=self.document)
                self.errors.update(validator.errors)

    def _validate_items_schema(self, schema, field, value):
        validator = self.__class__(schema)
        for item in value:
            validator.validate(item, context=self.document)
            for field, error in validator.errors.items():
                self._error(field, error)

    def _validate_dependencies(self, document, dependencies, field,
                               break_on_error=False):
        # handle cases where dependencies is a string or list of strings
        if isinstance(dependencies, _str_type):
            dependencies = [dependencies]

        if isinstance(dependencies, Sequence):
            for dependency in dependencies:
                if dependency not in document:
                    if not break_on_error:
                        self._error(field, errors.ERROR_DEPENDENCIES_FIELD %
                                    dependency)
                    else:
                        return False
        return True

    def _validate_validator(self, validator, field, value):
        # call customized validator function
        validator(field, value, self._error)
