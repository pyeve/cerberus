"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
"""

from collections import Callable, Hashable, Iterable, Mapping, MutableMapping,\
    Sequence
import copy
from datetime import datetime
import logging
import json
import re
import sys

from . import errors
from .utils import warn_deprecated

if sys.version_info[0] == 3:
    _str_type = str
    _int_types = (int,)
else:
    _str_type = basestring  # noqa
    _int_types = (int, long)  # noqa

log = logging.getLogger('cerberus')


class DocumentError(Exception):
    """ Raised when the target document is missing or has the wrong format """
    pass


class SchemaError(Exception):
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
       '*of'-rules can be extended by another rule
       'validation_rules'-property
       'rename'-rule renames a field to a given string
       'rename_handler'-rule for unknown fields
       'purge_unknown'-property and conditional purging of unknown fields added
       'trail'-property of Validator that relates the 'document' to
           'root_document'

    .. versionchanged:: 0.10

       refactoring

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
           validated document or 'None' if validation failed.

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
           instance of Validator-(sub-)class are passed to child-validators.
       Ensure that additional **kwargs of a subclass persist through
           validation.
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

    def __init__(self, *args, **kwargs):
        """ The arguments will be treated as with this signature:

        __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False,
                 purge_unknown=False)
        """

        self.document = None
        self._errors = {}
        self.root_document = None
        self.trail = ()
        self.update = False

        """ Assign args to kwargs and store configuration. """
        signature = ('schema', 'transparent_schema_rules',
                     'ignore_none_values', 'allow_unknown', 'purge_unknown')
        for i, p in enumerate(signature[:len(args)]):
            if p in kwargs:
                raise TypeError("__init__ got multiple values for argument "
                                "'%s'" % p)
            else:
                kwargs[p] = args[i]
        self.__config = kwargs

        self.validation_rules = self.__introspect_validation_rules()
        self._schema = DefinitionSchema(self, kwargs.get('schema', ()))

    def __introspect_validation_rules(self):
        rules = ['_'.join(x.split('_')[2:]) for x in dir(self)
                 if x.startswith('_validate')]
        return tuple(rules)

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

    def __get_child_validator(self, field=None, **kwargs):
        """ Creates a new instance of Validator-(sub-)class. All initial
        parameters of the parent are passed to the initialization, unless
        a parameter is given as an explicit *keyword*-parameter.

        :return: an instance of self.__class__
        """
        child_config = self.__config.copy()
        child_config.update(kwargs)
        child_validator = self.__class__(**child_config)
        child_validator.root_document = self.root_document or self.document
        if field is None:
            child_validator.trail = self.trail
        else:
            child_validator.trail = self.trail + (field, )
        return child_validator

    # Properties

    @property
    def allow_unknown(self):
        return self.__config.get('allow_unknown', False)

    @allow_unknown.setter
    def allow_unknown(self, value):
        self.__config['allow_unknown'] = value

    @property
    def errors(self):
        """
        The errors that were collected during the last processing of a
        document.

        :return: A list of processing errors.
        """
        return self._errors

    @property
    def ignore_none_values(self):
        return self.__config.get('ignore_none_values', False)

    @ignore_none_values.setter
    def ignore_none_values(self, value):
        self.__config['ignore_none_values'] = value

    @property
    def purge_unknown(self):
        return self.__config.get('purge_unknown', False)

    @purge_unknown.setter
    def purge_unknown(self, value):
        self.__config['purge_unknown'] = value

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = DefinitionSchema(self, schema)

    @property
    def transparent_schema_rules(self):
        return self.__config.get('transparent_schema_rules', False)

    @transparent_schema_rules.setter
    def transparent_schema_rules(self, value):
        self.__config['transparent_schema_rules'] = value

    # Document processing

    def __init_processing(self, document, schema=None):
        self._errors = {}
        self._unrequired_by_excludes = set()

        if schema is not None:
            self.schema = DefinitionSchema(self, schema)
        elif self.schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)
        if document is None:
            raise DocumentError(errors.ERROR_DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise DocumentError(
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
        document = document.copy()
        self.__init_processing(document, schema)
        result = self._normalize_mapping(document, schema or self.schema)
        if self.errors:
            return None
        else:
            return result

    def _normalize_mapping(self, mapping, schema):
        # TODO allow methods for coerce and rename_handler like validate_type
        mapping = self._rename_fields(mapping, schema)
        if self.purge_unknown:
            mapping = self._purge_unknown_fields(mapping, schema)
        mapping = self._coerce_values(mapping, schema)
        mapping = self._normalize_subdocuments(mapping, schema)
        return mapping

    def _coerce_values(self, mapping, schema):
        def coerce_value(coercer):
            try:
                mapping[field] = coercer(mapping[field])
            except (TypeError, ValueError):
                self._error(field,
                            errors.ERROR_COERCION_FAILED.format(field))

        for field in mapping:
            if field in schema and 'coerce' in schema[field]:
                coerce_value(schema[field]['coerce'])
            elif isinstance(self.allow_unknown, Mapping) and \
                    'coerce' in self.allow_unknown:
                coerce_value(self.allow_unknown['coerce'])

        return mapping

    def _normalize_subdocuments(self, mapping, schema):
        for field in mapping:
            if isinstance(mapping[field], Mapping):
                if 'propertyschema' in schema[field]:
                    self._normalize_mapping_per_propertyschema(
                        field, mapping, schema[field]['propertyschema'])
                if 'valueschema' in schema[field]:
                    self._normalize_mapping_per_valueschema(
                        field, mapping, schema[field]['valueschema'])
                if set(schema[field]) & set(('allow_unknown', 'purge_unknown',
                                             'schema')):
                    self._normalize_mapping_per_schema(field, mapping, schema)
        return mapping

    def _normalize_mapping_per_propertyschema(self, field, mapping,
                                              property_rules):
        child_schema = dict(((k, property_rules) for k in mapping[field]))
        document = dict(((k, k) for k in mapping[field]))
        validator = self.__get_child_validator(field,
                                               schema=child_schema)
        result = validator.normalized(document)
        for k in result:
            if result[k] in mapping[field]:
                log.warn("Normalizing keys of {path}: {key} already exists, "
                         "its value is replaced."
                         .format(path='.'.join(self.trail + (field,)), key=k))
                mapping[field][result[k]] = mapping[field][k]
            else:
                mapping[field][result[k]] = mapping[field][k]
                del mapping[field][k]

    def _normalize_mapping_per_valueschema(self, field, mapping, value_rules):
        validator = self.__get_child_validator(field, schema=(),
                                               allow_unknown=value_rules,
                                               purge_unknown=False)
        mapping[field] = validator.normalized(mapping[field])

    def _normalize_mapping_per_schema(self, field, mapping, schema):
        child_schema = schema[field].get('schema', dict())
        allow_unknown = schema[field].get('allow_unknown',
                                          self.allow_unknown)
        purge_unknown = schema[field].get('purge_unknown',
                                          self.purge_unknown)
        validator = self. \
            __get_child_validator(field,
                                  schema=child_schema,
                                  allow_unknown=allow_unknown,
                                  purge_unknown=purge_unknown)
        mapping[field] = validator.normalized(mapping[field])

    @staticmethod
    def _purge_unknown_fields(mapping, schema):
        for field in tuple(mapping):
            if field not in schema:
                del mapping[field]
        return mapping

    def _rename_fields(self, mapping, schema):
        for field in tuple(mapping):
            if field in schema:
                if 'rename' in schema[field]:
                    mapping[schema[field]['rename']] = mapping[field]
                    del mapping[field]
                elif 'rename_handler' in schema[field]:
                    new_name = schema[field]['rename_handler'](field)
                    mapping[new_name] = mapping[field]
                    del mapping[field]
            elif isinstance(self.allow_unknown, Mapping) and \
                    'rename_handler' in self.allow_unknown:
                new_name = self.allow_unknown['rename_handler'](field)
                mapping[new_name] = mapping[field]
                del mapping[field]
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
        self.update = update
        self.__init_processing(document, schema)
        self.__prepare_document(document, normalize)

        for field in self.document:
            if self.ignore_none_values and self.document[field] is None:
                continue
            definitions = self.schema.get(field)
            if definitions is not None:
                self.__validate_definitions(definitions, field)
            else:
                self.__validate_unknown_fields(field)

        if not self.update:
            self._validate_required_fields(self.document)

        return not bool(self._errors)

    __call__ = validate

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
        warn_deprecated('validate_update',
                        'Validator.validate_update is deprecated. '
                        'Use Validator.validate(update=True) instead.')
        return self.validate(document, schema, update=True)

    def __prepare_document(self, document, normalize):
        try:
            # might fail when dealing with complex document values
            self.document = copy.deepcopy(document)
        except:
            # fallback on a shallow copy
            self.document = document.copy()
        if normalize:
            self.document = self._normalize_mapping(document.copy(),
                                                    self.schema)
        else:
            self.document = document.copy()

    def __validate_unknown_fields(self, field):
        if self.allow_unknown:
            value = self.document[field]
            if isinstance(self.allow_unknown, Mapping):
                # validate that unknown fields matches the schema
                # for unknown_fields
                validator = self.__get_child_validator(
                    field, schema={field: self.allow_unknown})
                if not validator({field: value}, normalize=False):
                    self._error(field, validator.errors[field])
        else:
            self._error(field, errors.ERROR_UNKNOWN_FIELD)

    # Remember to keep the validations method below this line
    # sorted alphabetically

    def __validate_definitions(self, definitions, field):
        """ Validate a field's value against its defined rules. """

        def validate_rule(rule):
            validatorname = "_validate_" + rule.replace(" ", "_")
            validator = getattr(self, validatorname, None)
            if validator:
                return validator(definitions[rule], field, value)

        value = self.document[field]

        """ _validate_-methods must return True to abort validation. """
        if (self._validate_nullable(definitions, field, value) or
                self._validate_readonly(definitions, field, value) or
                self._validate_type(definitions, field, value) or
                self._validate_dependencies(definitions, field, value) or
                self._validate_schema(definitions, field, value)):
            return

        skip_rules = ('dependencies', 'coerce', 'schema', 'type')
        for rule in [x for x in definitions if x not in skip_rules]:
            validate_rule(rule)

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))
        elif isinstance(value, Sequence) and not isinstance(value, _str_type):
            unallowed = set(value) - set(allowed_values)
            if unallowed:
                self._error(
                    field,
                    errors.ERROR_UNALLOWED_VALUES.format(list(unallowed))
                )
        elif isinstance(value, int):
            if value not in allowed_values:
                self._error(field, errors.ERROR_UNALLOWED_VALUE.format(value))

    def _validate_dependencies(self, definition, field, value):
        dependencies = definition.get('dependencies')
        if dependencies is None:
            return

        if isinstance(dependencies, _str_type):
            dependencies = [dependencies]

        if isinstance(dependencies, Sequence):
            self.__validate_dependencies_sequence(dependencies, field)
        elif isinstance(dependencies, Mapping):
            self.__validate_dependencies_mapping(dependencies, field)

        if self.errors.get(field):
            return True

    def __validate_dependencies_mapping(self, dependencies, field):
        validated_deps = 0
        for dep_name, dep_values in dependencies.items():
            if (not isinstance(dep_values, Sequence) or
                    isinstance(dep_values, _str_type)):
                dep_values = [dep_values]
            context = self.document.copy()
            parts = dep_name.split('.')

            for part in parts:
                if part in context:
                    context = context[part]
                    if context in dep_values:
                        validated_deps += 1

        if validated_deps != len(dependencies):
            self._error(field, errors.ERROR_DEPENDENCIES_FIELD_VALUE
                        .format(dep_name, dep_values))

    def __validate_dependencies_sequence(self, dependencies, field):
        for dependency in dependencies:

            context = self.document.copy()
            parts = dependency.split('.')

            for part in parts:
                if part in context:
                    context = context[part]
                else:
                    self._error(field,
                                errors.ERROR_DEPENDENCIES_FIELD
                                .format(dependency))

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.ERROR_EMPTY_NOT_ALLOWED)

    def _validate_excludes(self, excludes, field, value):
        if isinstance(excludes, Hashable):
            excludes = [excludes]

        # Save required field to be checked latter
        if 'required' in self.schema[field] and self.schema[field]['required']:
            self._unrequired_by_excludes.add(field)
        for exclude in excludes:
            if (exclude in self.schema and
               'required' in self.schema[exclude] and
                    self.schema[exclude]['required']):

                self._unrequired_by_excludes.add(exclude)

        if [True for key in excludes if key in self.document]:
            # Wrap each field in `excludes` list between quotes
            exclusion_str = ', '.join("'{0}'"
                                      .format(word) for word in excludes)
            self._error(field,
                        errors.ERROR_EXCLUDES_FIELD.format(exclusion_str,
                                                           field))

    def _validate_items(self, items, field, value):
        if isinstance(items, Mapping):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, Sequence) and not isinstance(items, _str_type):
            self._validate_items_list(items, field, value)

    def _validate_items_list(self, items, field, values):
        if len(items) != len(values):
            self._error(field, errors.ERROR_ITEMS_LIST.format(len(items)))
        else:
            schema = dict((i, definition) for i, definition in enumerate(items))  # noqa
            validator = self.__get_child_validator(schema=schema)
            if not validator(dict((i, item) for i, item in enumerate(values))):
                self.errors.setdefault(field, {})
                self.errors[field].update(validator.errors)

    def _validate_items_schema(self, items, field, value):
        validator = self.__get_child_validator(schema=items)
        for item in value:
            validator(item, normalize=False)
            for field, error in validator.errors.items():
                self._error(field, error)

    def __validate_logical(self, operator, definitions, field, value):
        """ Validates value against all definitions and logs errors according
        to the operator.
        """
        if isinstance(definitions, Mapping):
            definitions = [definitions]

        valid_counter = 0
        errorstack = {}
        for i, definition in enumerate(definitions):
            s = self.schema[field].copy()
            del s[operator]
            s.update(definition)

            validator = self.__get_child_validator(schema={field: s})
            if validator({field: value}, normalize=False):
                valid_counter += 1
            errorstack["definition %d" % i] = \
                validator.errors.get(field, 'validated')

        if operator == 'anyof' and valid_counter < 1:
            e = {'anyof': 'no definitions validated'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'allof' and valid_counter < len(definitions):
            e = {'allof': 'one or more definitions did not validate'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'noneof' and valid_counter > 0:
            e = {'noneof': 'one or more definitions validated'}
            e.update(errorstack)
            self._error(field, e)
        if operator == 'oneof' and valid_counter != 1:
            e = {'oneof': 'more than one rule (or no rules) validated'}
            e.update(errorstack)
            self._error(field, e)

    def _validate_anyof(self, definitions, field, value):
        self.__validate_logical('anyof', definitions, field, value)

    def _validate_allof(self, definitions, field, value):
        self.__validate_logical('allof', definitions, field, value)

    def _validate_noneof(self, definitions, field, value):
        self.__validate_logical('noneof', definitions, field, value)

    def _validate_oneof(self, definitions, field, value):
        self.__validate_logical('oneof', definitions, field, value)

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

    def _validate_nullable(self, definition, field, value):
        if value is None:
            if definition.get("nullable", False):
                return True
            else:
                self._error(field, errors.ERROR_NOT_NULLABLE)
                return True

    def _validate_propertyschema(self, schema, field, value):
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                schema={field: {'schema': schema}})
            validator({field: list(value.keys())}, normalize=False)
            for error in validator.errors:
                self._error(field, error)

    def _validate_readonly(self, definition, field, value):
        if definition.get('readonly', False):
            self._error(field, errors.ERROR_READONLY_FIELD)
            if self.errors.get(field):
                return True

    def _validate_regex(self, pattern, field, value):
        if not isinstance(value, _str_type):
            return
        re_obj = re.compile(pattern)
        if not re_obj.match(value):
            self._error(field, errors.ERROR_REGEX.format(pattern))

    def _validate_required_fields(self, document):
        """ Validates that required fields are not missing. If dependencies
        are precised then validate 'required' only if all dependencies
        are validated.

        :param document: The document being validated.
        """
        required = set(field for field, definition in self.schema.items()
                       if definition.get('required') is True)
        required -= self._unrequired_by_excludes
        missing = required - set(field for field in document
                                 if document.get(field) is not None or
                                 not self.ignore_none_values)

        for field in missing:
            self._error(field, errors.ERROR_REQUIRED_FIELD)

        # At least on field from self._unrequired_by_excludes should be
        # present in document
        if self._unrequired_by_excludes:
            fields = set(field for field in document
                         if document.get(field) is not None)
            if self._unrequired_by_excludes.isdisjoint(fields):
                for field in self._unrequired_by_excludes - fields:
                    self._error(field, errors.ERROR_REQUIRED_FIELD)

    def _validate_schema(self, definition, field, value):
        schema = definition.get('schema')
        if schema is None:
            return

        if isinstance(value, Sequence) and not isinstance(value, _str_type):
            self.__validate_schema_sequence(field, schema, value)
        elif isinstance(value, Mapping):
            self.__validate_schema_mapping(field, schema, value,
                                           definition.get('allow_unknown',
                                                          self.allow_unknown))

    def __validate_schema_mapping(self, field, schema, value, allow_unknown):
        validator = self.__get_child_validator(field, schema=schema,
                                               allow_unknown=allow_unknown)
        if not validator(value, update=self.update, normalize=False):
            self._error(field, validator.errors)

    def __validate_schema_sequence(self, field, schema, value):
        list_errors = {}
        for i in range(len(value)):
            validator = self.__get_child_validator(
                schema={i: schema}, allow_unknown=self.allow_unknown)
            validator({i: value[i]}, normalize=False)
            list_errors.update(validator.errors)
        if len(list_errors):
            self._error(field, list_errors)

    def _validate_type(self, definition, field, value):
        def call_type_validation(_type, value):
            validator = getattr(self, "_validate_type_" + _type)
            validator(field, value)

        data_type = definition.get('type', None)
        if data_type is None:
            return

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

        if self.errors.get(field):
            return True

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
                validator({key: document}, {key: schema}, normalize=False)
                if len(validator.errors):
                    self._error(field, validator.errors)


class DefinitionSchema(MutableMapping):
    """ A dict-subclass for caching of validated schemas.

        .. versionadded:: 0.10
    """

    class Encoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Callable):
                return repr(o)
            return json.JSONEncoder.default(self, o)

    valid_schemas = set()

    def __init__(self, validator, schema=()):
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A definition-schema as ``dict``. Defaults to an empty
                      one.
        """
        schema = expand_definition_schema(schema)
        self.validator = validator
        self.validation_rules = validator.validation_rules
        self.schema = dict()
        self.update(schema)

    def __delitem__(self, key):
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
            self.__validate_on_update(_new_schema)
        except ValueError:
            raise SchemaError("Schema has no field '%s' defined" % key)
        except:
            raise
        else:
            del self.schema[key]

    def __getitem__(self, item):
        return self.schema[item]

    def __iter__(self):
        return iter(self.schema)

    def __len__(self):
        return len(self.schema)

    def __repr__(self):
        return str(self)

    def __setitem__(self, key, value):
        _new_schema = self.schema.copy()
        try:
            _new_schema.update({key: value})
            self.__validate_on_update(_new_schema)
        except:
            raise
        else:
            self.schema = _new_schema

    def __str__(self):
        return str(self.schema)

    def update(self, schema):
        try:
            _new_schema = self.schema.copy()
            _new_schema.update(schema)
            self.__validate_on_update(_new_schema)
        except ValueError:
            raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_TYPE
                              .format(schema))
        except:
            raise
        else:
            self.schema = _new_schema

    def __validate_on_update(self, schema):
        _hash = hash(repr(type(self.validator)) +
                     json.dumps(schema, cls=self.Encoder, sort_keys=True))
        if _hash not in self.valid_schemas:
            self.validate(schema)
            self.valid_schemas.add(_hash)

    def validate(self, schema=None):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.

        :return: The validated schema.

        .. versionadded:: 0.7.1
        """

        if schema is None:
            schema = self.schema

        for field, constraints in schema.items():
            if not isinstance(constraints, Mapping):
                raise SchemaError(errors.SCHEMA_ERROR_CONSTRAINT_TYPE
                                  .format(field))
            for constraint, value in constraints.items():
                # TODO reduce this boilerplate
                if constraint in ('nullable', 'readonly', 'required'):
                    if not isinstance(value, bool):
                        raise SchemaError(
                            '{}: {}: {}'.format(
                                field, constraint,
                                errors.ERROR_BAD_TYPE.format('boolean')))
                elif constraint == 'type':
                    self.__validate_type_definition(value)
                elif constraint == 'schema':
                    self.__validate_schema_definition(value)
                elif constraint == 'allow_unknown':
                    self.__validate_allow_unknown_definition(field, value)
                elif constraint == 'purge_unknown':
                    if not isinstance(value, bool):
                        raise SchemaError(errors
                                          .SCHEMA_ERROR_PURGE_UNKNOWN_TYPE
                                          .format(field))
                elif constraint in ('anyof', 'allof', 'noneof', 'oneof'):
                    self.__validate_definition_set(field, constraints,
                                                   constraint, value)
                elif constraint == 'items':
                    if isinstance(value, Mapping):
                        # TODO remove on next major release
                        # list of dicts, deprecated
                        warn_deprecated('items_dict',
                                        "The 'items'-rule with a mapping as "
                                        "constraint is deprecated. Use the "
                                        "'schema'-rule instead.")
                        DefinitionSchema(self.validator, value)
                    else:
                        for item_schema in value:
                            DefinitionSchema(self.validator,
                                             {'schema': item_schema})
                elif constraint == 'dependencies':
                    self.__validate_dependencies_definition(field, value)
                elif constraint in ('coerce', 'rename_handler', 'validator'):
                    if not isinstance(value, Callable):
                        raise SchemaError(
                            errors.SCHEMA_ERROR_CALLABLE_TYPE
                            .format(field))
                elif constraint == 'rename':
                    if not isinstance(value, Hashable):
                        raise SchemaError(errors.SCHEMA_ERROR_RENAME_TYPE
                                          .format(field))
                elif constraint == 'excludes':
                    self.__validate_excludes_definition(value)
                elif constraint not in self.validation_rules:
                    if not self.validator.transparent_schema_rules:
                            raise SchemaError(errors.SCHEMA_ERROR_UNKNOWN_RULE
                                              .format(constraint, field))

    def __validate_allow_unknown_definition(self, field, value):
        if isinstance(value, bool):
            pass
        elif isinstance(value, Mapping):
            DefinitionSchema(self.validator, {field: value})
        else:
            raise SchemaError(errors.SCHEMA_ERROR_ALLOW_UNKNOWN_TYPE
                              .format(field))

    def __validate_definition_set(self, field, constraints, constraint, value):
        if not isinstance(value, Sequence) and \
                not isinstance(value, _str_type):
            raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_SET_TYPE
                              .format(constraint, field))

        for of_constraint in value:
            c = constraints.copy()
            del c[constraint]
            c.update(of_constraint)
            DefinitionSchema(self.validator, {field: c})

    def __validate_dependencies_definition(self, field, value):
        if not isinstance(value, (Mapping, Sequence)) and \
                not isinstance(value, _str_type):
            raise SchemaError(errors.SCHEMA_ERROR_DEPENDENCY_TYPE)
        for dependency in value:
            if not isinstance(dependency, _str_type):
                raise SchemaError(errors.SCHEMA_ERROR_DEPENDENCY_VALIDITY
                                  .format(dependency, field))

    def __validate_excludes_definition(self, excludes):
        if isinstance(excludes, Hashable):
            excludes = [excludes]
        for key in excludes:
            if not isinstance(key, _str_type):
                raise SchemaError(
                    errors.SCHEMA_ERROR_EXCLUDES_HASHABLE.format(key))

    def __validate_schema_definition(self, value):
        try:  # if mapping
            DefinitionSchema(self.validator, value)
        except SchemaError:  # if sequence
            DefinitionSchema(self.validator, {'schema': value})

    def __validate_type_definition(self, type_defs):
        type_defs = type_defs if isinstance(type_defs, list) else [type_defs]
        for type_def in type_defs:
            if not 'type_' + type_def in self.validation_rules:
                raise SchemaError(
                    errors.ERROR_UNKNOWN_TYPE.format(type_def))


def expand_definition_schema(schema):
    """ Expand agglutinated rules in a definition-schema.

    :param schema: The schema-definition to expand.

    :return: The expanded schema-definition.

    .. versionadded:: 0.10
    """

    # TODO remove on next major release
    def update_to_valueschema(constraints):
        if not isinstance(constraints, Mapping):
            return constraints
        if 'keyschema' in constraints:
            constraints['valueschema'] = constraints['keyschema']
            del constraints['keyschema']
            warn_deprecated('keyschema', "The 'keyschema'-rule is deprecated. "
                                         "Use 'valueschema' instead.")
        for key, value in constraints.items():
            constraints[key] = update_to_valueschema(value)
        return constraints

    def is_of_rule(rule):
        for operator in ('allof', 'anyof', 'noneof', 'oneof'):
            if isinstance(rule, _str_type) and rule.startswith(operator + '_'):
                return True
        return False

    def has_mapping_schema(field):
        if isinstance(field, Mapping):
            if 'schema' in field:
                if isinstance(field['schema'], Mapping):
                    if not field['schema'] or \
                            isinstance(tuple(field['schema'].values())[0],
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
