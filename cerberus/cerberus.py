"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/
"""

import sys
import re
import copy
from datetime import datetime
from collections import Iterable, Mapping, Sequence
from . import errors

if sys.version_info[0] == 3:
    _str_type = str
    _int_types = (int,)
else:
    _str_type = basestring  # noqa
    _int_types = (int, long)  # noqa


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
                               checking. (no UnknownType error will be added).
                               Defaults to ``False``. Useful if your document
                               is composed from function kwargs with defaults.
    :param allow_unknown: if ``True`` unknown key/value pairs (not present in
                          the schema) will be ignored, and validation will
                          pass. Defaults to ``False``, returning an 'unknown
                          field error' un validation.

    .. versionchanged:: 0.9.2
       only perform shallow copies in order to avoid issues with Python 2.6
       way to handle deepcopy on BytesIO (and in general, complex objects).
       Closes #147.

    .. versionchanged:: 0.9.1
       'required' will always be validated, regardless of any dependencies.

    .. versionadded:: 0.9
       'anyof', 'noneof', 'allof', 'anyof' validation rules.
       PyPy support.
       'coerce' rule.
       'propertyschema' validation rule.
       'validator.validated' takes a document as argument and returns a
       Validated document or 'None' if validation failed.

    .. versionchanged:: 0.9
       Use 'str.format' in error messages so if someone wants to override them
           does not get an excpetion if arguments are not passed.
       'keyschema' is renamed to 'valueschema'. Closes #92.
       'type' can be a list of valid types.
       Usages of 'document' to 'self.document' in '_validate'.
       When 'items' is applied to a list, field name is used as key for
           'validator.errors', and offending field indexes are used as keys for
       Field errors ({'a_list_of_strings': {1: 'not a string'}})
       Additional kwargs that are passed to the __init__-method of an
       Instance of Validator-(sub-)class are passed to child-validators.
       Ensure that additional **kwargs of a subclass persist through validation
       Improve failure message when testing against multiple types.
       Ignore 'keyschema' when not a mapping.
       Ignore 'schema' when not a sequence.
       'allow_unknown' can also be set for nested dicts. Closes #75.
       Raise SchemaError when an unallowed 'type' is used in conjunction with
           'schema' rule.


    .. versionchanged:: 0.8.1
       'dependencies' for sub-document fields. Closes #64.
       'readonly' should be validated before any other validation. Closes #63.
       'allow_unknown' does not apply to sub-dictionaries in a list.
       Closes #67.
       update mode does not ignore required fields in subdocuments. Closes #72.
       'allow_unknown' does not respect custom rules. Closes #66.

    .. versionadded:: 0.8
       'dependencies' also support a dict of dependencies.
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
    special_rules = "required", "nullable", "type", "dependencies", \
                    "readonly", "allow_unknown", "schema", "coerce"

    def __init__(self, *args, **kwargs):
        signature = ('schema', 'transparent_schema_rules',
                     'ignore_none_values', 'allow_unknown')
        for i, p in enumerate(signature[:len(args)]):
            if p in kwargs:
                raise TypeError("__init__ got multiple values for argument "
                                "'%s'" % p)
            else:
                kwargs[p] = args[i]

        self.__config = kwargs
        self.schema = kwargs.get('schema')
        self.transparent_schema_rules = kwargs.get('transparent_schema_rules',
                                                   False)
        self.ignore_none_values = kwargs.get('ignore_none_values', False)
        self.allow_unknown = kwargs.get('allow_unknown', False)

        if self.schema:
            self.validate_schema(self.schema)
        self._errors = {}
        self._current = None

    def __call__(self, *args, **kwargs):
        return self.validate(*args, **kwargs)

    @property
    def current(self):
        """Get the current document being validated.

        When validating, the current (sub)document will be available
        via this property.
        """
        return self._current

    @property
    def errors(self):
        """
        :rtype: a list of validation errors. Will be empty if no errors
                were found during. Resets after each call to :func:`validate`.
        """
        return self._errors

    def validate_update(self, document, schema=None, context=None):
        """ Validates a Python dictionary against a validation schema. The
        difference with :func:`validate` is that the ``required`` rule will be
        ignored here.

        :param schema: optional validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantiation.
        :param context: the context in which the document should be validated.
                        Defaults to ``None``.

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
                       class instantiation.
        :param update: If ``True`` validation of required fields won't be
                       performed.
        :param context: the document in which context validation should be
                        performed. Defaults to ``None``.

        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors` property for a list of validation errors.

        .. versionchanged:: 0.4.0
           Support for update mode.
        """
        return self._validate(document, schema, update=update, context=context)

    def validated(self, *args, **kwargs):
        """ Wrapper around ``Validator.validate`` that returns the validated
        document or ``None`` if validation failed.
        """
        self.validate(*args, **kwargs)
        if self.errors:
            return None
        else:
            return self.document

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
            raise ValidationError(
                errors.ERROR_DOCUMENT_FORMAT.format(document))

        # make root document available for validators (Cerberus #42, Eve #295)
        if not context:
            self.document = copy.copy(document)
            self._current = self.document
        else:
            self.document = context
            self._current = document

        # copy keys since the document might change during its iteration
        for field in [f for f in self._current]:
            value = self._current[field]

            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition is not None:
                self._validate_definition(definition, field, value)
            else:
                if self.allow_unknown:
                    if isinstance(self.allow_unknown, Mapping):
                        # validate that unknown fields matches the schema
                        # for unknown_fields
                        unknown_validator = \
                            self.__get_child_validator(
                                schema={field: self.allow_unknown})
                        if not unknown_validator.validate({field: value}):
                            self._error(field, unknown_validator.errors[field])
                    else:
                        # allow unknown field to pass without any kind of
                        # validation
                        pass
                else:
                    self._error(field, errors.ERROR_UNKNOWN_FIELD)

        if not self.update:
            self._validate_required_fields(self._current)

        return len(self._errors) == 0

    def _validate_definition(self, definition, field, value):
        if value is None:
            if definition.get("nullable", False) is True:
                return
            else:
                self._error(field, errors.ERROR_NOT_NULLABLE)

        if 'coerce' in definition:
            value = self._validate_coerce(definition['coerce'], field,
                                          value)
            self.document[field] = value

        if 'readonly' in definition:
            self._validate_readonly(definition['readonly'], field,
                                    value)
            if self.errors.get(field):
                return

        if 'type' in definition:
            self._validate_type(definition['type'], field, value)
            if self.errors.get(field):
                return

        if 'dependencies' in definition:
            self._validate_dependencies(
                document=self.document,
                dependencies=definition["dependencies"],
                field=field
            )
            if self.errors.get(field):
                return

        if 'schema' in definition:
            self._validate_schema(definition['schema'],
                                  field,
                                  value,
                                  definition.get('allow_unknown'))

        definition_rules = [rule for rule in definition.keys()
                            if rule not in self.special_rules]
        for rule in definition_rules:
            validatorname = "_validate_" + rule.replace(" ", "_")
            validator = getattr(self, validatorname, None)
            if validator:
                validator(definition[rule], field, value)

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
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT.format(schema))

        # TODO remove on next major release
        def update_to_valueschema(schema, warning_printed=False):
            if 'keyschema' in schema:
                schema['valueschema'] = schema['keyschema']
                del schema['keyschema']
                if not warning_printed:
                    print('WARNING cerberus: `keyschema` is deprecated, '
                          'use `valueschema` instead')
                    warning_printed = True
            for key, value in schema.items():
                if isinstance(value, Mapping):
                    schema[key] = update_to_valueschema(value, warning_printed)
            return schema
        schema = update_to_valueschema(schema)

        for field, constraints in schema.items():
            if not isinstance(constraints, Mapping):
                raise SchemaError(errors.ERROR_DEFINITION_FORMAT.format(field))
            for constraint, value in constraints.items():
                if constraint == 'type':
                    values = value if isinstance(value, list) else [value]
                    for value in values:
                        if not hasattr(self, '_validate_type_' + value):
                            raise SchemaError(
                                errors.ERROR_UNKNOWN_TYPE.format(value))
                    if 'dict' in values and 'list' in values:
                        if 'valueschema' in constraints and \
                            'schema' not in constraints:  # noqa
                                raise SchemaError('You must provide a compleme'
                                                  'ntary `schema`')
                        if 'schema' in constraints and \
                            'valueschema' not in constraints:  # noqa
                                raise SchemaError('You must provide a compleme'
                                                  'ntary `valueschema`')
                elif constraint == 'schema':
                    constraint_type = constraints.get('type')
                    if constraint_type is not None:
                        if constraint_type == 'list' or \
                                'list' in constraint_type:
                            self.validate_schema({'schema': value})
                        elif constraint_type == 'dict' or \
                                'dict' in constraint_type:
                            self.validate_schema(value)
                    else:
                        raise SchemaError(
                            errors.ERROR_SCHEMA_TYPE.format(field))
                elif constraint in self.special_rules:
                    pass
                elif constraint in ('anyof', 'allof', 'noneof', 'oneof'):
                    if(isinstance(value, Sequence) and
                       not isinstance(value, _str_type)):
                        # make sure each definition in an
                        # anyof/allof constraint validates
                        for v in value:
                            # get a copy of the schema with
                            # anyof/allof replaced with their value
                            s = copy.copy(constraints)
                            del s[constraint]
                            s.update(v)
                            self.validate_schema({field: s})
                    else:
                        self.validate_schema({field: [value]})
                elif constraint == 'items':
                    if isinstance(value, Mapping):
                        # list of dicts, deprecated
                        self.validate_schema(value)
                    else:
                        for item_schema in value:
                            self.validate_schema({'schema': item_schema})
                elif not hasattr(self, '_validate_' + constraint):
                    if not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE.format(
                                constraint, field))

    def _validate_coerce(self, coerce, field, value):
        try:
            value = coerce(value)
        except (TypeError, ValueError):
            self._error(field, errors.ERROR_COERCION_FAILED.format(field))
        return value

    def _validate_required_fields(self, document):
        """ Validates that required fields are not missing. If dependencies
        are precised then validate 'required' only if all dependencies
        are validated.

        :param document: the document being validated.
        """
        required = list(field for field, definition in self.schema.items()
                        if definition.get('required') is True)
        missing = set(required) - set(key for key in document.keys()
                                      if document.get(key) is not None or
                                      not self.ignore_none_values)

        for field in missing:
            self._error(field, errors.ERROR_REQUIRED_FIELD)

    def _validate_readonly(self, read_only, field, value):
        if read_only:
            self._error(field, errors.ERROR_READONLY_FIELD)

    def _validate_regex(self, match, field, value):
        """
        .. versionadded:: 0.7
        """
        if not isinstance(value, _str_type):
            return
        pattern = re.compile(match)
        if not pattern.match(value):
            self._error(field, errors.ERROR_REGEX.format(match))

    def _validate_type(self, data_type, field, value):

        def call_type_validation(_type, value):
            validator = getattr(self, "_validate_type_" + _type)
            validator(field, value)

        if isinstance(data_type, _str_type):
            call_type_validation(data_type, value)
        elif isinstance(data_type, Iterable):
            prev_errors = self._errors.copy()

            for _type in data_type:
                call_type_validation(_type, value)
                if len(self._errors) == len(prev_errors):
                    return
                else:
                    self._errors = prev_errors.copy()
            self._error(field, errors.ERROR_BAD_TYPE.format(", ".
                        join(data_type[:-1]) + ' or ' + data_type[-1]))

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE.format("string"))

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("integer"))

    def _validate_type_float(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("float"))

    def _validate_type_number(self, field, value):
        """
        .. versionadded:: 0.6
        """
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("number"))

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(field, errors.ERROR_BAD_TYPE.format("boolean"))

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(field, errors.ERROR_BAD_TYPE.format("datetime"))

    def _validate_type_dict(self, field, value):
        if not isinstance(value, Mapping):
            self._error(field, errors.ERROR_BAD_TYPE.format("dict"))

    def _validate_type_list(self, field, value):
        if not isinstance(value, Sequence) or isinstance(
                value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE.format("list"))

    def _validate_type_set(self, field, value):
        if not isinstance(value, set):
            self._error(field, errors.ERROR_BAD_TYPE.format("set"))

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, Sequence):
            if len(value) > max_length:
                self._error(field, errors.ERROR_MAX_LENGTH.format(max_length))

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, Sequence):
            if len(value) < min_length:
                self._error(field, errors.ERROR_MIN_LENGTH.format(min_length))

    def _validate_max(self, max_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value > max_value:
                self._error(field, errors.ERROR_MAX_VALUE.format(max_value))

    def _validate_min(self, min_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value < min_value:
                self._error(field, errors.ERROR_MIN_VALUE.format(min_value))

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))
        elif isinstance(value, Sequence):
            disallowed = set(value) - set(allowed_values)
            if disallowed:
                self._error(
                    field,
                    errors.ERROR_UNALLOWED_VALUES.format(list(disallowed))
                )
        elif isinstance(value, int):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.ERROR_EMPTY_NOT_ALLOWED)

    def _validate_schema(self, schema, field, value, nested_allow_unknown):
        if isinstance(value, Sequence) and not isinstance(value, _str_type):
            list_errors = {}
            for i in range(len(value)):
                validator = self.__get_child_validator(
                    schema={i: schema}, allow_unknown=self.allow_unknown)
                validator.validate({i: value[i]}, context=self.document)
                list_errors.update(validator.errors)
            if len(list_errors):
                self._error(field, list_errors)
        elif isinstance(value, Mapping):
            if 'list' in self.schema[field]['type']:
                return
            validator = copy.copy(self)
            validator.schema = schema
            if not validator.allow_unknown:
                validator.allow_unknown = nested_allow_unknown
            validator.validate(value, context=self.document,
                               update=self.update)
            if len(validator.errors):
                self._error(field, validator.errors)

    def _validate_valueschema(self, schema, field, value):
        if isinstance(value, Mapping):
            for key, document in value.items():
                validator = self.__get_child_validator()
                validator.validate(
                    {key: document}, {key: schema}, context=self.document)
                if len(validator.errors):
                    self._error(field, validator.errors)

    def _validate_propertyschema(self, schema, field, value):
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                schema={field: {'type': 'list', 'schema': schema}})
            validator.validate({field: list(value.keys())},
                               context=self.document)
            for error in validator.errors:
                self._error(field, error)

    def _validate_items(self, items, field, value):
        if isinstance(items, Mapping):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, Sequence):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, schema, field, values):
        if len(schema) != len(values):
            self._error(field, errors.ERROR_ITEMS_LIST.format(len(schema)))
        else:
            for i in range(len(schema)):
                validator = self.__get_child_validator(schema={i: schema[i]})
                validator.validate({i: values[i]}, context=self.document)
                for error in validator.errors:
                    self.errors.setdefault(field, {})
                    self.errors[field].update(validator.errors)

    def _validate_items_schema(self, schema, field, value):
        validator = self.__get_child_validator(schema=schema)
        for item in value:
            validator.validate(item, context=self.document)
            for field, error in validator.errors.items():
                self._error(field, error)

    def _validate_dependencies(self, document, dependencies, field,
                               break_on_error=False):
        if isinstance(dependencies, _str_type):
            dependencies = [dependencies]

        if isinstance(dependencies, Sequence):
            for dependency in dependencies:
                parts = dependency.split('.')
                subdoc = copy.copy(document)
                for part in parts:
                    if part not in subdoc:
                        if not break_on_error:
                            self._error(field,
                                        errors.ERROR_DEPENDENCIES_FIELD
                                        .format(dependency))
                        else:
                            return False
                    else:
                        subdoc = subdoc[part]

        elif isinstance(dependencies, Mapping):
            for dep_name, dep_values in dependencies.items():
                if isinstance(dep_values, _str_type):
                    dep_values = [dep_values]
                parts = dep_name.split('.')
                subdoc = copy.copy(document)
                for part in parts:
                    if part not in subdoc:
                        if not break_on_error:
                            self._error(
                                field,
                                errors.ERROR_DEPENDENCIES_FIELD_VALUE.format(
                                    (dep_name, dep_values))
                            )
                            break
                        else:
                            return False
                    else:
                        subdoc = subdoc[part]
                if isinstance(subdoc, _str_type) and subdoc not in dep_values:
                    if not break_on_error:
                        self._error(
                            field,
                            errors.ERROR_DEPENDENCIES_FIELD_VALUE.format(
                                (dep_name, dep_values))
                        )
                    else:
                        return False

        return True

    def _validate_validator(self, validator, field, value):
        # call customized validator function
        validator(field, value, self._error)

    def _validate_logical(self, operator, definitions, field, value):
        # validates value against each definition in definitions
        if isinstance(definitions, Mapping):
            definitions = [definitions]

        # count the number of definitions that validate
        valid = 0
        errorstack = {}
        for i in range(len(definitions)):
            definition = definitions[i]
            # create a schema instance with the rules in definition
            s = copy.copy(self.schema[field])
            del s[operator]
            s.update(definition)
            # get a child validator to do our work
            v = self.__get_child_validator(schema={field: s})
            if v.validate({field: value}):
                valid += 1
            errorstack["definition %d" % i] = \
                v.errors.get(field, 'validated')

        if operator == 'anyof' and valid < 1:
            e = {'anyof': 'no definitions validated'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'allof' and valid < len(definitions):
            e = {'allof': 'one or more definitions did not validate'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'noneof' and valid > 0:
            e = {'noneof': 'one or more definitions validated'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'oneof' and valid != 1:
            e = {'oneof': 'more than one rule (or no rules) validated'}
            e.update(errorstack)
            self._error(field, e)

    def _validate_anyof(self, definitions, field, value):
        self._validate_logical('anyof', definitions, field, value)

    def _validate_allof(self, definitions, field, value):
        self._validate_logical('allof', definitions, field, value)

    def _validate_noneof(self, definitions, field, value):
        self._validate_logical('noneof', definitions, field, value)

    def _validate_oneof(self, definitions, field, value):
        self._validate_logical('oneof', definitions, field, value)

    def __get_child_validator(self, **kwargs):
        """ creates a new instance of Validator-(sub-)class, all initial
        parameters of the parent are passed to the initialization, unless
        a parameter is given as an explicit *keyword*-parameter.

        :rtype: an instance of self.__class__"""
        child_config = self.__config.copy()
        child_config.update(kwargs)
        return self.__class__(**child_config)
