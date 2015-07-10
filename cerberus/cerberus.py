"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
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
    """ Validator class. Normalizes and validates any mapping against a
    validation-schema which is provided as an argument at class instantiation
    or upon calling the :func:`validate`, :func:`validated` or
    :func:`normalized` method.

    :param schema: Optional validation schema, can also be provided upon
                   processing.
    :param transparent_schema_rules: If ``True`` unknown schema rules will be
                                     ignored; no SchemaError will be raised.
                                     Defaults to ``False``. Useful you need to
                                     extend the schema grammar beyond Cerberus'
                                     domain.
    :param ignore_none_values: If ``True`` it will ignore fields with``None``-
                               values when validating. Defaults to ``False``.
                               Useful if your document is composed from
                               function-kwargs with ``None``-defaults.
    :param allow_unknown: If ``True`` unknown fields that are not defined in
                          the schema will be ignored.
                          If a ``dict`` with a definition-schema is given, any
                          undefined field will be validated against its rules.
                          Defaults to ``False``.


    .. versionadded:: 0.10
       'normalized'-method

    .. versionchanged:: 0.10

       some refactoring

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
           does not get an exception if arguments are not passed.
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
        """ The arguments will be treated as with this signature:

        __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False)
        """
        signature = ('schema', 'transparent_schema_rules',
                     'ignore_none_values', 'allow_unknown')
        for i, p in enumerate(signature[:len(args)]):
            if p in kwargs:
                raise TypeError("__init__ got multiple values for argument "
                                "'%s'" % p)
            else:
                kwargs[p] = args[i]

        self.__config = kwargs
        self.allow_unknown = kwargs.get('allow_unknown', False)
        self.ignore_none_values = kwargs.get('ignore_none_values', False)
        self.schema = kwargs.get('schema')
        self.transparent_schema_rules = kwargs.get('transparent_schema_rules',
                                                   False)

        self._errors = {}
        self.root_document = None
        self.document = None
        self.update = False
        if self.schema:
            self.schema = expand_definition_schema(self.schema)
            self.validate_definition_schema(self.schema)
        self._errors = {}

    def __call__(self, *args, **kwargs):
        return self.validate(*args, **kwargs)

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

    def __get_child_validator(self, **kwargs):
        """ Creates a new instance of Validator-(sub-)class. All initial
        parameters of the parent are passed to the initialization, unless
        a parameter is given as an explicit *keyword*-parameter.

        :return: an instance of self.__class__
        """
        child_config = self.__config.copy()
        child_config.update(kwargs)
        child_validator = self.__class__(**child_config)
        child_validator.root_document = self.root_document or self.document
        return child_validator

    # Properties

    @property
    def errors(self):
        """
        The errors that were collected during the last processing of a
        document.

        :return: A list of processing errors.
        """
        return self._errors

    # Schema validation

    def validate_definition_schema(self, schema):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.

        :return: The validated schema.

        .. versionadded:: 0.7.1
        """

        if not isinstance(schema, Mapping):
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT.format(schema))

        for field, constraints in schema.items():
            if not isinstance(constraints, Mapping):
                raise SchemaError(errors.ERROR_DEFINITION_FORMAT.format(field))
            for constraint, value in constraints.items():
                if constraint == 'type':
                    type_defs = value if isinstance(value, list) else [value]
                    for type_def in type_defs:
                        if not hasattr(self, '_validate_type_' + type_def):
                            raise SchemaError(
                                errors.ERROR_UNKNOWN_TYPE.format(type_def))
                elif constraint == 'schema':
                    try:
                        self.validate_definition_schema(value)
                    except SchemaError:
                        self.validate_definition_schema({'schema': value})
                elif constraint in self.special_rules:
                    pass
                elif constraint in ('anyof', 'allof', 'noneof', 'oneof'):
                    if(isinstance(value, Sequence) and
                       not isinstance(value, _str_type)):
                        for v in value:
                            # get a copy of the schema where the logical
                            # operator is replaced with their value
                            s = copy.copy(constraints)
                            del s[constraint]
                            s.update(v)
                            self.validate_definition_schema({field: s})
                    else:
                        self.validate_definition_schema({field: [value]})
                elif constraint == 'items':
                    if isinstance(value, Mapping):
                        # TODO remove on next major release
                        # list of dicts, deprecated
                        self.validate_definition_schema(value)
                    else:
                        for item_schema in value:
                            self.validate_definition_schema({'schema':
                                                             item_schema})
                elif not hasattr(self, '_validate_' + constraint):
                    if not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE.format(
                                constraint, field))

        return schema

    # Document processing

    def __init_processing(self, document, schema=None):
        self._errors = {}
        if schema is not None:
            schema = expand_definition_schema(schema)
            self.schema = self.validate_definition_schema(schema)
        elif self.schema is None:
            raise SchemaError(errors.ERROR_SCHEMA_MISSING)
        if document is None:
            raise ValidationError(errors.ERROR_DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise ValidationError(
                errors.ERROR_DOCUMENT_FORMAT.format(document))
        self.root_document = self.root_document or document

    # # Normalizing

    def normalized(self, document, schema=None):
        """ Returns the document normalized according to the specified rules
        of a schema.

        :param document: The mapping to normalize.
        :param schema: The validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantiation.

        :return: A normalized copy of the provided mapping or ``None`` if an
                 error occurred during normalization.
        """
        self.__init_processing(document, schema)
        result = self._normalize_mapping(document, schema or self.schema)
        if self.errors:
            return None
        else:
            return result

    def _normalize_mapping(self, mapping, schema):
        # TODO implement renaming of fields
        # TODO implement purging of unknown fields

        for field in mapping:
            if field in schema and 'coerce' in schema[field]:
                try:
                    mapping[field] = schema[field]['coerce'](mapping[field])
                except (TypeError, ValueError):
                    self._error(field,
                                errors.ERROR_COERCION_FAILED.format(field))

            if isinstance(mapping[field], Mapping) and 'schema' in schema[field]:  # noqa
                validator = self.__get_child_validator(schema=schema[field]
                                                       ['schema'])
                mapping[field] = validator.normalized(mapping[field])

        return mapping

    # # Validating

    def validate(self, document, schema=None, update=False, normalize=True):
        """ Normalizes and validates a mapping against a validation-schema of
        defined rules.

        :param document: The mapping to validate.
        :param schema: The validation-schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantiation.
        :param update: If ``True`` required fields won't be checked.
        :param normalize: If ``True`` (default), normalize the document before
                          validation.

        :return: ``True`` if validation succeeds, otherwise ``False``. Check
                 the :func:`errors` property for a list of processing errors.

        .. versionchanged:: 0.10
           Removed 'context'-argument, Validator takes care of setting it now.
           It's accessible as ``self.root_document``.

        .. versionchanged:: 0.4.0
           Support for update mode.
        """
        self.__init_processing(document, schema)
        self.update = update

        try:
            # might fail when dealing with complex document values
            self.document = copy.deepcopy(document)
        except:
            # fallback on a shallow copy
            self.document = copy.copy(document)
        if normalize:
            self.document = self._normalize_mapping(self.document,
                                                    self.schema)

        for field in self.document:
            value = self.document[field]

            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition is not None:
                self.__validate_definition(definition, field, value)
            else:
                if self.allow_unknown:
                    if isinstance(self.allow_unknown, Mapping):
                        # validate that unknown fields matches the schema
                        # for unknown_fields
                        unknown_validator = \
                            self.__get_child_validator(
                                schema={field: self.allow_unknown})
                        if not unknown_validator.validate({field: value},
                                                          normalize=False):
                            self._error(field, unknown_validator.errors[field])
                else:
                    self._error(field, errors.ERROR_UNKNOWN_FIELD)

        if not self.update:
            self._validate_required_fields(self.document)

        return not bool(self._errors)

    def validated(self, *args, **kwargs):
        """ Wrapper around :func:`validate` that returns the normalized and
        validated document or ``None`` if validation failed.
        """
        self.validate(*args, **kwargs)
        if self.errors:
            return None
        else:
            return self.document

    # TODO remove on next major release
    def validate_update(self, document, schema=None):
        """ Validates a Python dictionary against a validation schema. The
        difference with :func:`validate` is that the ``required`` rule will be
        ignored here.

        :param schema: Optional validation schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantiation.

        :return: True if validation succeeds, False otherwise. Check the
                 :func:`errors`-property for a list of validation errors.

        .. deprecated:: 0.4.0
           Use :func:`validate` with ``update=True`` instead.
        """
        return self.validate(document, schema, update=True)

    def __validate_definition(self, definition, field, value):
        """ Validate a field's value against its defined rules. """
        if value is None:
            if definition.get("nullable", False) is True:
                return
            else:
                self._error(field, errors.ERROR_NOT_NULLABLE)

        if 'readonly' in definition and definition['readonly']:
            self._error(field, errors.ERROR_READONLY_FIELD)
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
                                  definition.get('allow_unknown',
                                                 self.allow_unknown))

        definition_rules = [rule for rule in definition
                            if rule not in self.special_rules]
        for rule in definition_rules:
            validatorname = "_validate_" + rule.replace(" ", "_")
            validator = getattr(self, validatorname, None)
            if validator:
                validator(definition[rule], field, value)

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))
        elif isinstance(value, Sequence) and not isinstance(value, _str_type):
            disallowed = set(value) - set(allowed_values)
            if disallowed:
                self._error(
                    field,
                    errors.ERROR_UNALLOWED_VALUES.format(list(disallowed))
                )
        elif isinstance(value, int):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))

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

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.ERROR_EMPTY_NOT_ALLOWED)

    def _validate_items(self, items, field, value):
        if isinstance(items, Mapping):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, Sequence) and not isinstance(items, _str_type):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, items, field, values):
        if len(items) != len(values):
            self._error(field, errors.ERROR_ITEMS_LIST.format(len(items)))
        else:
            for i, item_definition in enumerate(items):
                validator =\
                    self.__get_child_validator(schema={i: item_definition})
                if not validator.validate({i: values[i]}, normalize=False):
                    self.errors.setdefault(field, {})
                    self.errors[field].update(validator.errors)

    def _validate_items_schema(self, items, field, value):
        validator = self.__get_child_validator(schema=items)
        for item in value:
            validator.validate(item, normalize=False)
            for field, error in validator.errors.items():
                self._error(field, error)

    def _validate_logical(self, operator, definitions, field, value):
        """ Validates value against all definitions and logs errors according
        to the operator.
        """
        if isinstance(definitions, Mapping):
            definitions = [definitions]

        # count the number of definitions that validate
        valid = 0
        errorstack = {}
        for i, definition in enumerate(definitions):
            # create a schema instance with the rules in definition
            s = copy.copy(self.schema[field])
            del s[operator]
            s.update(definition)
            # get a child validator to do our work
            v = self.__get_child_validator(schema={field: s})
            if v.validate({field: value}, normalize=False):
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

    def _validate_max(self, max_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value > max_value:
                self._error(field, errors.ERROR_MAX_VALUE.format(max_value))

    def _validate_min(self, min_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value < min_value:
                self._error(field, errors.ERROR_MIN_VALUE.format(min_value))

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, Sequence):
            if len(value) > max_length:
                self._error(field, errors.ERROR_MAX_LENGTH.format(max_length))

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, Sequence):
            if len(value) < min_length:
                self._error(field, errors.ERROR_MIN_LENGTH.format(min_length))

    def _validate_propertyschema(self, schema, field, value):
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                schema={field: {'type': 'list', 'schema': schema}})
            validator.validate({field: list(value.keys())}, normalize=False)
            for error in validator.errors:
                self._error(field, error)

    def _validate_regex(self, match, field, value):
        """
        .. versionadded:: 0.7
        """
        if not isinstance(value, _str_type):
            return
        pattern = re.compile(match)
        if not pattern.match(value):
            self._error(field, errors.ERROR_REGEX.format(match))

    def _validate_required_fields(self, document):
        """ Validates that required fields are not missing. If dependencies
        are precised then validate 'required' only if all dependencies
        are validated.

        :param document: The document being validated.
        """
        required = set(field for field, definition in self.schema.items()
                       if definition.get('required') is True)
        missing = required - set(field for field in document
                                 if document.get(field) is not None or
                                 not self.ignore_none_values)

        for field in missing:
            self._error(field, errors.ERROR_REQUIRED_FIELD)

    def _validate_schema(self, schema, field, value, allow_unknown):
        if isinstance(value, Sequence) and not isinstance(value, _str_type):
            list_errors = {}
            for i in range(len(value)):
                validator = self.__get_child_validator(
                    schema={i: schema}, allow_unknown=self.allow_unknown)
                validator.validate({i: value[i]}, normalize=False)
                list_errors.update(validator.errors)
            if len(list_errors):
                self._error(field, list_errors)
        elif isinstance(value, Mapping):
            if 'list' in self.schema[field]['type']:
                return
            validator = self.__get_child_validator(schema=schema,
                                                   allow_unknown=allow_unknown)
            if not validator.validate(value, update=self.update,
                                      normalize=False):
                self._error(field, validator.errors)

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

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(field, errors.ERROR_BAD_TYPE.format("boolean"))

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(field, errors.ERROR_BAD_TYPE.format("datetime"))

    def _validate_type_dict(self, field, value):
        if not isinstance(value, Mapping):
            self._error(field, errors.ERROR_BAD_TYPE.format("dict"))

    def _validate_type_float(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("float"))

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("integer"))

    def _validate_type_list(self, field, value):
        if not isinstance(value, Sequence) or isinstance(
                value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE.format("list"))

    def _validate_type_number(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.ERROR_BAD_TYPE.format("number"))

    def _validate_type_set(self, field, value):
        if not isinstance(value, set):
            self._error(field, errors.ERROR_BAD_TYPE.format("set"))

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(field, errors.ERROR_BAD_TYPE.format("string"))

    def _validate_validator(self, validator, field, value):
        # call customized validator function
        validator(field, value, self._error)

    def _validate_valueschema(self, schema, field, value):
        if isinstance(value, Mapping):
            for key, document in value.items():
                validator = self.__get_child_validator()
                validator.validate({key: document}, {key: schema},
                                   normalize=False)
                if len(validator.errors):
                    self._error(field, validator.errors)


def expand_definition_schema(schema):
    """ Expand agglutinated rules in a definition-schema.

    :param schema: The schema-definition to expand.

    :return: The expanded schema-definition.

    .. versionadded:: 0.10
    """

    # TODO remove on next major release
    def update_to_valueschema(constraints, warning_printed=False):
        if not isinstance(constraints, Mapping):
            return constraints
        if 'keyschema' in constraints:
            constraints['valueschema'] = constraints['keyschema']
            del constraints['keyschema']
            if not warning_printed:
                print('WARNING cerberus: `keyschema` is deprecated, '
                      'use `valueschema` instead')
                warning_printed = True
        for key, value in constraints.items():
            constraints[key] = update_to_valueschema(value, warning_printed)
        return constraints

    def is_of_rule(rule):
        for operator in ('allof', 'anyof', 'noneof', 'oneof'):
            if rule.startswith(operator + '_'):
                return True
        return False

    def has_mapping_schema(field):
        if isinstance(field, Mapping):
            if 'schema' in field:
                if isinstance(field['schema'], Mapping):
                    if isinstance(tuple(field['schema'].values())[0],
                                  Mapping):
                        return True
        return False

    for field in schema:
        # TODO remove on next major release
        try:
            schema[field] = update_to_valueschema(schema[field])
        except TypeError:
            return schema  # bad schema will fail on validation

        try:
            of_rules = [x for x in schema[field] if is_of_rule(x)]
        except TypeError:
            return schema  # bad schema will fail on validation

        for of_rule in of_rules:
            operator, rule = of_rule.split('_')
            schema[field].update({operator: []})
            for value in schema[field][of_rule]:
                schema[field][operator].append({rule: value})
            del schema[field][of_rule]

        if has_mapping_schema(schema[field]):
                schema[field]['schema'] = \
                    expand_definition_schema(schema[field]['schema'])

        if 'valueschema' in schema[field]:
            schema[field]['valueschema'] = \
                expand_definition_schema(
                    {'x': schema[field]['valueschema']})['x']

        for rule in ('allof', 'anyof', 'items', 'noneof', 'oneof'):
            # TODO remove instance-check at next major-release
            if rule in schema[field] and isinstance(schema[field][rule],
                                                    Sequence):
                new_rules_definition = []
                for item in schema[field][rule]:
                    new_rules_definition\
                        .append(expand_definition_schema({'x': item})['x'])
                schema[field][rule] = new_rules_definition

    return schema
