"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
"""

from collections import Callable, Hashable, Iterable, Mapping, MutableMapping,\
    Sequence
from datetime import datetime
import json
import logging
import re

from . import errors
from .platform import _str_type, _int_types
from .utils import drop_item_from_tuple, warn_deprecated


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
    :param purge_unknown: If ``True`` unknown fields will be deleted from the
                          document unless a validation is called with disabled
                          normalization.
    :param error_handler: The error handler that formats the result of
                          ``errors``. May be an instance or a class.
                          Default: :class:`cerberus.errors.BasicErrorHandler`.
    :param error_handler_config: A dictionary the is passed to the inizializa-
                                 tion of the error handler. Defaults to an
                                 empty one.


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

    mandatory_validations = ('nullable', )
    priority_validations = ('nullable', 'readonly', 'type')

    def __init__(self, *args, **kwargs):
        """ The arguments will be treated as with this signature:

        __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False,
                 purge_unknown=False, error_handler=errors.BasicErrorHandler,
                 error_handler_config=dict())
        """

        self.document = None
        self._errors = []
        self.document_error_tree = errors.DocumentErrorTree()
        self.schema_error_tree = errors.SchemaErrorTree()
        self.root_document = None
        self.root_schema = None
        self.document_path = ()
        self.schema_path = ()
        self.update = False

        error_handler = kwargs.pop('error_handler', errors.BasicErrorHandler)
        eh_config = kwargs.pop('error_handler_config', dict())
        if issubclass(error_handler, errors.BaseErrorHandler):
            self.error_handler = error_handler(**eh_config)
        elif isinstance(error_handler, errors.BaseErrorHandler):
            self.error_handler = error_handler
        else:
            raise RuntimeError('Invalid error_handler.')

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

        self.validation_rules = self.__introspect_rules_to('validate')
        self.normalization_rules = self.__introspect_rules_to('normalize')
        self._schema = DefinitionSchema(self, kwargs.get('schema', ()))

    def __introspect_rules_to(self, rule_type):
        rules = ['_'.join(x.split('_')[2:]) for x in dir(self)
                 if x.startswith('_' + rule_type)]
        return tuple(rules)

    def _error(self, *args):
        """ Creates and adds one or multiple errors.
        :param args: Either an iterable of ValidationError-instances, a field's
                     name and an error message or a field's name, a reference
                     to a defined error and supplemental information.

                     Iterable of errors:
                     Expects an iterable of :class:`errors.Validation error`
                     instances.
                     The errors will be added to the errors stash
                     :attr:`_errors` of self.

                     Field's name and error message:
                     Expects two strings as arguments, the first is the field's
                     name, the second the error message.
                     A custom error will be created containing the message.
                     There will however be fewer information contained in the
                     error (no reference to the violated rule and its
                     constraint).

                     Field's name, error reference and suppl. information:
                     Expects:
                     - the invalid field's name as string
                     - the error-reference, see :mod:`errors`
                     - arbitrary, supplemental information about the error
        """
        if len(args) == 1:
            self._errors.extend(args[0])
            self._errors.sort()
            for error in args[0]:
                self.document_error_tree += error
                self.schema_error_tree += error
        elif len(args) == 2 and isinstance(args[1], _str_type):
            self._error(args[0], errors.CUSTOM, args[1])
        elif len(args) >= 2:
            field = args[0]
            code = args[1].code
            rule = args[1].rule
            info = args[2:]

            document_path = self.document_path + (field, )

            schema_path = self.schema_path
            if code != errors.UNKNOWN_FIELD.code and rule is not None:
                schema_path += (field, rule)

            if rule == 'nullable':
                constraint = self.schema[field].get(rule, False)
            else:
                constraint = self.schema[field][rule] if rule else None

            value = self.document.get(field)

            error = errors.ValidationError(document_path, schema_path,
                                           code, rule, constraint,
                                           value, info)
            self._error([error])

    def __get_child_validator(self, document_crumb=None, schema_crumb=None,
                              **kwargs):
        """ Creates a new instance of Validator-(sub-)class. All initial
        parameters of the parent are passed to the initialization, unless
        a parameter is given as an explicit *keyword*-parameter.

        :return: an instance of self.__class__
        """
        child_config = self.__config.copy()
        child_config.update(kwargs)
        child_validator = self.__class__(**child_config)

        child_validator.root_document = self.root_document or self.document
        child_validator.root_schema = self.root_schema or self.schema

        if document_crumb is None:
            child_validator.document_path = self.document_path
        else:
            if not isinstance(document_crumb, tuple):
                document_crumb = (document_crumb, )
            child_validator.document_path = self.document_path + document_crumb

        if schema_crumb is None:
            child_validator.schema_path = self.schema_path
        else:
            if not isinstance(schema_crumb, tuple):
                schema_crumb = (schema_crumb, )
            child_validator.schema_path = self.schema_path + schema_crumb

        return child_validator

    def _drop_nodes_from_errorpaths(self, errors, dp_items, sp_items):
        """ Removes nodes by index from an errorpath, relatively to the
            basepaths of self.

        :param errors: A list of :class:`errors.ValidationError` instances.
        :param dp_items: A list of integers, pointing at the nodes to drop from
                         the :attr:`document_path`.
        :param sp_items: Alike ``dp_items``, but for :attr:`schema_path`.
        """
        dp_basedepth = len(self.document_path)
        sp_basedepth = len(self.schema_path)
        for error in errors:
            for i in sorted(dp_items, reverse=True):
                error.document_path = \
                    drop_item_from_tuple(error.document_path, dp_basedepth+i)
            for i in sorted(sp_items, reverse=True):
                error.schema_path = \
                    drop_item_from_tuple(error.schema_path, sp_basedepth+i)
            if error.child_errors:
                self._drop_nodes_from_errorpaths(error.child_errors,
                                                 dp_items, sp_items)

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
        Returns the errors of the last processing formatted by the handler that
        is bound to :attr:`error_handler` of self.
        """
        return self.error_handler(self._errors)

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
        self._errors = []
        self._unrequired_by_excludes = set()

        if schema is not None:
            self.schema = DefinitionSchema(self, schema)
        elif self.schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)
        if document is None:
            raise DocumentError(errors.DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise DocumentError(
                errors.DOCUMENT_FORMAT.format(document))
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
        self.__normalize_mapping(document, schema or self.schema)
        if self._errors:
            return None
        else:
            return document

    def __normalize_mapping(self, mapping, schema):
        # TODO allow methods for coerce and rename_handler like validate_type
        self.__normalize_rename_fields(mapping, schema)
        if self.purge_unknown:
            self._normalize_purge_unknown(mapping, schema)
        self._normalize_default(mapping, schema)
        self._normalize_coerce(mapping, schema)
        self.__normalize_containers(mapping, schema)
        return mapping

    def _normalize_coerce(self, mapping, schema):
        def coerce_value(coercer):
            try:
                mapping[field] = coercer(mapping[field])
            except (TypeError, ValueError):
                self._error(field, errors.COERCION_FAILED)

        for field in mapping:
            if field in schema and 'coerce' in schema[field]:
                coerce_value(schema[field]['coerce'])
            elif isinstance(self.allow_unknown, Mapping) and \
                    'coerce' in self.allow_unknown:
                coerce_value(self.allow_unknown['coerce'])

    def __normalize_containers(self, mapping, schema):
        for field in mapping:
            if field not in schema:
                continue
            if isinstance(mapping[field], Mapping):
                if 'propertyschema' in schema[field]:
                    self.__normalize_mapping_per_propertyschema(
                        field, mapping, schema[field]['propertyschema'])
                if 'valueschema' in schema[field]:
                    self.__normalize_mapping_per_valueschema(
                        field, mapping, schema[field]['valueschema'])
                if set(schema[field]) & set(('allow_unknown', 'purge_unknown',
                                             'schema')):
                    self.__normalize_mapping_per_schema(field, mapping, schema)
            elif isinstance(mapping[field], Sequence) and \
                not isinstance(mapping[field], _str_type) and \
                    'schema' in schema[field]:
                self.__normalize_sequence(field, mapping, schema)

    def __normalize_mapping_per_propertyschema(self, field, mapping,
                                               property_rules):
        schema = dict(((k, property_rules) for k in mapping[field]))
        document = dict(((k, k) for k in mapping[field]))
        validator = self.__get_child_validator(
            document_crumb=(field,), schema_crumb=(field, 'propertyschema'),
            schema=schema)
        result = validator.normalized(document)
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2, 4])
            self._error(validator._errors)
        for k in result:
            if result[k] == mapping[field][k]:
                continue
            if result[k] in mapping[field]:
                log.warn("Normalizing keys of {path}: {key} already exists, "
                         "its value is replaced."
                         .format(path='.'.join(self.document_path + (field,)),
                                 key=k))
                mapping[field][result[k]] = mapping[field][k]
            else:
                mapping[field][result[k]] = mapping[field][k]
                del mapping[field][k]

    def __normalize_mapping_per_valueschema(self, field, mapping, value_rules):
        schema = dict(((k, value_rules) for k in mapping[field]))
        validator = self.__get_child_validator(
            document_crumb=field, schema_crumb=(field, 'valueschema'),
            schema=schema)
        mapping[field] = validator.normalized(mapping[field])
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(validator._errors)

    def __normalize_mapping_per_schema(self, field, mapping, schema):
        child_schema = schema[field].get('schema', dict())
        allow_unknown = schema[field].get('allow_unknown',
                                          self.allow_unknown)
        purge_unknown = schema[field].get('purge_unknown',
                                          self.purge_unknown)
        validator = self. \
            __get_child_validator(document_crumb=field,
                                  schema_crumb=(field, 'schema'),
                                  schema=child_schema,
                                  allow_unknown=allow_unknown,
                                  purge_unknown=purge_unknown)
        mapping[field] = validator.normalized(mapping[field])
        if validator._errors:
            self._error(validator._errors)

    def __normalize_sequence(self, field, mapping, schema):
        child_schema = dict(((k, schema[field]['schema'])
                             for k in range(len(mapping[field]))))
        validator = self.__get_child_validator(document_crumb=field,
                                               schema_crumb=(field, 'schema'),
                                               schema=child_schema)
        result = validator.normalized(dict((k, v) for k, v
                                           in enumerate(mapping[field])))
        for i in result:
            mapping[field][i] = result[i]
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(validator._errors)

    @staticmethod
    def _normalize_purge_unknown(mapping, schema):
        for field in tuple(mapping):
            if field not in schema:
                del mapping[field]
        return mapping

    def __normalize_rename_fields(self, mapping, schema):
        for field in tuple(mapping):
            if field in schema:
                self._normalize_rename(mapping, schema, field)
                self._normalize_rename_handler(mapping, schema, field)
            elif isinstance(self.allow_unknown, Mapping) and \
                    'rename_handler' in self.allow_unknown:
                new_name = self.allow_unknown['rename_handler'](field)
                mapping[new_name] = mapping[field]
                del mapping[field]
        return mapping

    def _normalize_rename(self, mapping, schema, field):
        if 'rename' in schema[field]:
            mapping[schema[field]['rename']] = mapping[field]
            del mapping[field]

    def _normalize_rename_handler(self, mapping, schema, field):
        if 'rename_handler' in schema[field]:
            new_name = schema[field]['rename_handler'](field)
            mapping[new_name] = mapping[field]
            del mapping[field]

    def _normalize_default(self, mapping, schema):
        for field in tuple(schema):
            nullable = schema[field].get('nullable', False)
            if 'default' in schema[field] and \
                    (field not in mapping or
                     mapping[field] is None and not nullable):
                mapping[field] = schema[field]['default']

    # # Validating

    def validate(self, document, schema=None, update=False, normalize=True):
        """ Normalizes and validates a mapping against a validation-schema of
        defined rules.

        :param document: The mapping to validate.
        :param schema: The validation-schema. Defaults to ``None``. If not
                       provided here, the schema must have been provided at
                       class instantiation.
        :param update: If ``True``, required fields won't be checked.
        :param normalize: If ``True``, normalize the document before validation.

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
        if self._errors:
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
        self.document = document.copy()  # needed by _error
        if normalize:
            self.document = self.__normalize_mapping(document.copy(),
                                                     self.schema)

    def __validate_unknown_fields(self, field):
        if self.allow_unknown:
            value = self.document[field]
            if isinstance(self.allow_unknown, Mapping):
                # validate that unknown fields matches the schema
                # for unknown_fields
                validator = self.__get_child_validator(
                    schema_crumb='allow_unknown',
                    schema={field: self.allow_unknown})
                if not validator({field: value}, normalize=False):
                    self._error(validator._errors)
        else:
            self._error(field, errors.UNKNOWN_FIELD)

    # Remember to keep the validations method below this line
    # sorted alphabetically

    def __validate_definitions(self, definitions, field):
        """ Validate a field's value against its defined rules. """

        def validate_rule(rule):
            validatorname = "_validate_" + rule.replace(" ", "_")
            validator = getattr(self, validatorname, None)
            if validator:
                return validator(definitions.get(rule, None), field, value)

        value = self.document[field]

        """ _validate_-methods must return True to abort validation. """
        prior_rules = tuple((x for x in self.priority_validations
                             if x in definitions
                             or x in self.mandatory_validations))
        for rule in prior_rules:
            if validate_rule(rule):
                return

        rules = set(self.mandatory_validations)
        rules |= set(definitions.keys())
        rules -= set(prior_rules + self.normalization_rules +
                     ('allow_unknown', 'required'))
        for rule in rules:
            validate_rule(rule)

    def _validate_allowed(self, allowed_values, field, value):
        if isinstance(value, _str_type):
            if value not in allowed_values:
                self._error(field, errors.UNALLOWED_VALUE, value)
        elif isinstance(value, Sequence) and not isinstance(value, _str_type):
            unallowed = set(value) - set(allowed_values)
            if unallowed:
                self._error(field, errors.UNALLOWED_VALUES, list(unallowed))
        elif isinstance(value, int):
            if value not in allowed_values:
                self._error(field, errors.UNALLOWED_VALUE, value)

    def _validate_dependencies(self, dependencies, field, value):
        if isinstance(dependencies, _str_type):
            dependencies = [dependencies]

        if isinstance(dependencies, Sequence):
            self.__validate_dependencies_sequence(dependencies, field)
        elif isinstance(dependencies, Mapping):
            self.__validate_dependencies_mapping(dependencies, field)

        if self.document_error_tree.fetch_node_from(
                self.schema_path + (field, 'dependencies')) is not None:
            return True

    def __validate_dependencies_mapping(self, dependencies, field):
        validated_deps = 0
        for dep_name, dep_values in dependencies.items():
            if (not isinstance(dep_values, Sequence) or
                    isinstance(dep_values, _str_type)):
                dep_values = [dep_values]
            context = self.document.copy()
            parts = dep_name.split('.')
            info = dict()

            for part in parts:
                if part in context:
                    context = context[part]
                    if context in dep_values:
                        validated_deps += 1
                    else:
                        info.update({dep_name: context})

        if validated_deps != len(dependencies):
            self._error(field, errors.DEPENDENCIES_FIELD_VALUE, info)

    def __validate_dependencies_sequence(self, dependencies, field):
        for dependency in dependencies:

            context = self.document.copy()
            parts = dependency.split('.')

            for part in parts:
                if part in context:
                    context = context[part]
                else:
                    self._error(field, errors.DEPENDENCIES_FIELD, dependency)

    def _validate_empty(self, empty, field, value):
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.EMPTY_NOT_ALLOWED)

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
            self._error(field, errors.EXCLUDES_FIELD, exclusion_str)

    # TODO remove on next major release
    def _validate_items(self, items, field, value):
        if isinstance(items, Mapping):
            self._validate_items_schema(items, field, value)
        elif isinstance(items, Sequence) and not isinstance(items, _str_type):
            self._validate_items_list(items, field, value)

    # TODO rename to _validate_items on next major release
    def _validate_items_list(self, items, field, values):
        if len(items) != len(values):
            self._error(field, errors.ITEMS_LENGTH, len(items), len(values))
        else:
            schema = dict((i, definition) for i, definition in enumerate(items))  # noqa
            validator = self.__get_child_validator(document_crumb=field,
                                                   schema_crumb=(field, 'items'),  # noqa
                                                   schema=schema)
            if not validator(dict((i, item) for i, item in enumerate(values)),
                             normalize=False):
                self._error(field, errors.BAD_ITEMS, validator._errors)

    # TODO remove on next major release
    def _validate_items_schema(self, items, field, value):
        validator = self.__get_child_validator(schema=items)
        for item in value:
            if not validator(item, normalize=False):
                self._error(validator._errors)

    def __validate_logical(self, operator, definitions, field, value):
        """ Validates value against all definitions and logs errors according
        to the operator.
        """
        if isinstance(definitions, Mapping):
            definitions = [definitions]

        valid_counter = 0
        _errors = []

        for i, definition in enumerate(definitions):
            s = self.schema[field].copy()
            del s[operator]
            s.update(definition)

            validator = self.__get_child_validator(
                schema_crumb=(field, operator, i),
                schema={field: s})
            if validator({field: value}, normalize=False):
                valid_counter += 1
            else:
                self._drop_nodes_from_errorpaths(validator._errors, [], [3])
                _errors.extend(validator._errors)

        if operator == 'anyof' and valid_counter < 1:
            self._error(field, errors.ANYOF, _errors,
                        valid_counter, len(definitions))
        elif operator == 'allof' and valid_counter < len(definitions):
            self._error(field, errors.ALLOF, _errors,
                        valid_counter, len(definitions))
        elif operator == 'noneof' and valid_counter > 0:
            self._error(field, errors.NONEOF, _errors,
                        valid_counter, len(definitions))
        elif operator == 'oneof' and valid_counter != 1:
            self._error(field, errors.ONEOF, _errors,
                        valid_counter, len(definitions))

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
                self._error(field, errors.MAX_VALUE)

    def _validate_min(self, min_value, field, value):
        if isinstance(value, (_int_types, float)):
            if value < min_value:
                self._error(field, errors.MIN_VALUE)

    def _validate_maxlength(self, max_length, field, value):
        if isinstance(value, Sequence):
            if len(value) > max_length:
                self._error(field, errors.MAX_LENGTH)

    def _validate_minlength(self, min_length, field, value):
        if isinstance(value, Sequence):
            if len(value) < min_length:
                self._error(field, errors.MIN_LENGTH)

    def _validate_nullable(self, nullable, field, value):
        if value is None:
            if nullable:
                return True
            else:
                self._error(field, errors.NOT_NULLABLE)
                return True

    def _validate_propertyschema(self, schema, field, value):
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                document_crumb=(field,),
                schema_crumb=(field, 'propertyschema'),
                schema=dict(((k, schema) for k in value.keys())))
            if not validator(dict(((k, k) for k in value.keys())),
                             normalize=False):
                self._drop_nodes_from_errorpaths(validator._errors,
                                                 [], [2, 4])
                self._error(field, errors.PROPERTYSCHEMA, validator._errors)

    def _validate_readonly(self, readonly, field, value):
        if readonly:
            self._error(field, errors.READONLY_FIELD)
            return True

    def _validate_regex(self, pattern, field, value):
        if not isinstance(value, _str_type):
            return
        if not pattern.endswith('$'):
            pattern += '$'
        re_obj = re.compile(pattern)
        if not re_obj.match(value):
            self._error(field, errors.REGEX_MISMATCH)

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
            self._error(field, errors.REQUIRED_FIELD)

        # At least on field from self._unrequired_by_excludes should be
        # present in document
        if self._unrequired_by_excludes:
            fields = set(field for field in document
                         if document.get(field) is not None)
            if self._unrequired_by_excludes.isdisjoint(fields):
                for field in self._unrequired_by_excludes - fields:
                    self._error(field, errors.REQUIRED_FIELD)

    def _validate_schema(self, schema, field, value):
        if schema is None:
            return

        if isinstance(value, Sequence) and not isinstance(value, _str_type):
            self.__validate_schema_sequence(field, schema, value)
        elif isinstance(value, Mapping):
            self.__validate_schema_mapping(field, schema, value)

    def __validate_schema_mapping(self, field, schema, value):
        allow_unknown = self.schema[field].get('allow_unknown',
                                               self.allow_unknown)
        validator = self.__get_child_validator(document_crumb=field,
                                               schema_crumb=(field, 'schema'),
                                               schema=schema,
                                               allow_unknown=allow_unknown)
        if not validator(value, update=self.update, normalize=False):
            self._error(validator._errors)

    def __validate_schema_sequence(self, field, schema, value):
        schema = dict(((i, schema) for i in range(len(value))))
        validator = self.__get_child_validator(
            document_crumb=field, schema_crumb=(field, 'schema'),
            schema=schema, allow_unknown=self.allow_unknown)
        validator(dict(((i, v) for i, v in enumerate(value))), normalize=False)
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(field, errors.SEQUENCE_SCHEMA, validator._errors)

    def _validate_type(self, data_type, field, value):
        def call_type_validation(_type, value):
            # TODO refactor to a less complex code on next major release
            # validator = getattr(self, "_validate_type_" + _type)
            # return validator(field, value)

            prev_errors = len(self._errors)
            validator = getattr(self, "_validate_type_" + _type)
            validator(field, value)
            if len(self._errors) == prev_errors:
                return True
            else:
                return False

        if isinstance(data_type, _str_type):
            if call_type_validation(data_type, value):
                return
        elif isinstance(data_type, Iterable):
            # TODO simplify this when methods don't submit errors
            validator = self.__get_child_validator(
                schema={'turing': {'anyof': [{'type': x} for x in data_type]}})
            if validator({'turing': value}):
                return
            else:
                self._error(field, errors.BAD_TYPE)
        return True

    def _validate_type_boolean(self, field, value):
        if not isinstance(value, bool):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_datetime(self, field, value):
        if not isinstance(value, datetime):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_dict(self, field, value):
        if not isinstance(value, Mapping):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_float(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_integer(self, field, value):
        if not isinstance(value, _int_types):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_list(self, field, value):
        if not isinstance(value, Sequence) or isinstance(
                value, _str_type):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_number(self, field, value):
        if not isinstance(value, float) and not isinstance(value, _int_types):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_set(self, field, value):
        if not isinstance(value, set):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(field, errors.BAD_TYPE)

    def _validate_validator(self, validator, field, value):
        # call customized validator function
        validator(field, value, self._error)

    def _validate_valueschema(self, schema, field, value):
        schema_crumb = (field, 'valueschema')
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                document_crumb=field, schema_crumb=schema_crumb,
                schema=dict((k, schema) for k in value))
            validator(value, normalize=False)
            if validator._errors:
                self._drop_nodes_from_errorpaths(validator._errors, [], [2])
                self._error(field, errors.VALUESCHEMA, validator._errors)


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
        self.rules = validator.validation_rules + validator.normalization_rules
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
                     json.dumps(self.__cast_keys_to_strings(schema),
                                cls=self.Encoder, sort_keys=True))
        if _hash not in self.valid_schemas:
            self.validate(schema)
            self.valid_schemas.add(_hash)

    def __cast_keys_to_strings(self, mapping):
        result = dict()
        for key in mapping:
            if isinstance(mapping[key], Mapping):
                value = self.__cast_keys_to_strings(mapping[key])
            else:
                value = mapping[key]
            result[str(type(key)) + str(key)] = value
        return result

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
                                errors.BAD_TYPE.format('boolean')))
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
                elif constraint in ('propertyschema', 'valueschema'):
                    if set(value) & set(('rename', 'rename_handler')):
                        raise SchemaError(errors.SCHEMA_ERROR_XSCHEMA_RENAME)
                elif constraint not in self.rules:
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
            if not 'type_' + type_def in self.rules:
                raise SchemaError(
                    errors.SCHEMA_ERROR_UNKNOWN_TYPE.format(type_def))


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
