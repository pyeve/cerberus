"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
"""

from ast import literal_eval
from collections import Hashable, Iterable, Mapping, Sequence
from copy import copy
from datetime import datetime
import re
from warnings import warn

from . import errors
from .platform import _str_type, _int_types
from .schema import DefinitionSchema, SchemaError
from .utils import drop_item_from_tuple, isclass


toy_error_handler = errors.ToyErrorHandler()


def dummy_for_rule_validation(rule_constraints):
    def dummy(self, constraint, field, value):
        raise RuntimeError('Dummy method called. Its purpose is to hold just'
                           'validation constraints for a rule.')
    f = dummy
    f.__doc__ = rule_constraints
    return f


class DocumentError(Exception):
    """ Raised when the target document is missing or has the wrong format """
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

    _inspected_classed = set()
    is_child = False
    mandatory_validations = ('nullable', )
    priority_validations = ('nullable', 'readonly', 'type')
    _valid_schemas = set()

    def __new__(cls, *args, **kwargs):
        if cls not in cls._inspected_classed:
            cls.__set_introspection_properties()
            cls._inspected_classed.add(cls)
        return super(Validator, cls).__new__(cls)

    @classmethod
    def __set_introspection_properties(cls):
        def attributes_with_prefix(prefix):
            rules = ['_'.join(x.split('_')[2:]) for x in dir(cls)
                     if x.startswith('_' + prefix)]
            return tuple(rules)

        cls.types, cls.validation_rules, cls.validators = (), {}, ()
        for attribute in attributes_with_prefix('validate'):
            if attribute.startswith('type_'):
                cls.types += (attribute[len('type_'):],)
            elif attribute.startswith('validator_'):
                cls.validators += (attribute[len('validator_'):],)
            else:
                constraints = getattr(cls, '_validate_' + attribute).__doc__
                constraints = {} if constraints is None \
                    else literal_eval(constraints.lstrip())
                cls.validation_rules[attribute] = constraints

        cls.validation_rules['type']['allowed'] = cls.types
        x = cls.validation_rules['validator']['anyof']
        x[1]['schema']['oneof'][1]['allowed'] = x[2]['allowed'] = cls.validators

        cls.coercers, cls.normalization_rules = (), {}
        for attribute in attributes_with_prefix('normalize'):
            if attribute.startswith('coerce_'):
                cls.coercers += (attribute[len('coerce_'):],)
            else:
                constraints = getattr(cls, '_normalize_' + attribute).__doc__
                constraints = {} if constraints is None \
                    else literal_eval(constraints.lstrip())
                cls.normalization_rules[attribute] = constraints

        for rule in ('coerce', 'rename_handler'):
            x = cls.normalization_rules[rule]['anyof']
            x[1]['schema']['oneof'][1]['allowed'] = \
                x[2]['allowed'] = cls.coercers

        cls.rules = {}
        cls.rules.update(cls.validation_rules)
        cls.rules.update(cls.normalization_rules)

    def __init__(self, *args, **kwargs):
        """ The arguments will be treated as with this signature:

        __init__(self, schema=None, transparent_schema_rules=False,
                 ignore_none_values=False, allow_unknown=False,
                 purge_unknown=False, error_handler=errors.BasicErrorHandler,
                 error_handler_config=dict())
        """

        self.document = None
        self._errors = errors.ErrorsList()
        self.document_error_tree = errors.DocumentErrorTree()
        self.schema_error_tree = errors.SchemaErrorTree()
        self.root_document = None
        self.root_schema = None
        self.document_path = ()
        self.schema_path = ()
        self.update = False
        self.__init_error_handler(kwargs)
        self.__store_config(args, kwargs)
        self.schema = kwargs.get('schema', None)
        self.allow_unknown = kwargs.get('allow_unknown', False)

    def __init_error_handler(self, kwargs):
        error_handler = kwargs.pop('error_handler', errors.BasicErrorHandler)
        eh_config = kwargs.pop('error_handler_config', dict())
        if isclass(error_handler) and \
                issubclass(error_handler, errors.BaseErrorHandler):
            self.error_handler = error_handler(**eh_config)
        elif isinstance(error_handler, errors.BaseErrorHandler):
            self.error_handler = error_handler
        else:
            raise RuntimeError('Invalid error_handler.')

    def __store_config(self, args, kwargs):
        """ Assign args to kwargs and store configuration. """
        signature = ('schema', 'transparent_schema_rules',
                     'ignore_none_values', 'allow_unknown', 'purge_unknown')
        for i, p in enumerate(signature[:len(args)]):
            if p in kwargs:
                raise TypeError("__init__ got multiple values for argument "
                                "'%s'" % p)
            else:
                kwargs[p] = args[i]
        self._config = kwargs

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
                self.error_handler.emit(error)
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
        child_config = self._config.copy()
        child_config.update(kwargs)
        if not self.is_child:
            child_config['is_child'] = True
            child_config['error_handler'] = toy_error_handler
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

    def __get_rule_handler(self, domain, rule):
        methodname = '_{0}_{1}'.format(domain, rule.replace(' ', '_'))
        return getattr(self, methodname, None)

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
                    drop_item_from_tuple(error.document_path, dp_basedepth + i)
            for i in sorted(sp_items, reverse=True):
                error.schema_path = \
                    drop_item_from_tuple(error.schema_path, sp_basedepth + i)
            if error.child_errors:
                self._drop_nodes_from_errorpaths(error.child_errors,
                                                 dp_items, sp_items)

    # Properties

    @property
    def allow_unknown(self):
        return self._config.get('allow_unknown', False)

    @allow_unknown.setter
    def allow_unknown(self, value):
        if not isinstance(value, (bool, DefinitionSchema)):
            DefinitionSchema(self, {'allow_unknown': value})
        self._config['allow_unknown'] = value

    @property
    def errors(self):
        """
        Returns the errors of the last processing formatted by the handler that
        is bound to :attr:`error_handler` of self.
        """
        return self.error_handler(self._errors)

    @property
    def ignore_none_values(self):
        return self._config.get('ignore_none_values', False)

    @ignore_none_values.setter
    def ignore_none_values(self, value):
        self._config['ignore_none_values'] = value

    @property
    def is_child(self):
        return self._config.get('is_child', False)

    @property
    def purge_unknown(self):
        return self._config.get('purge_unknown', False)

    @purge_unknown.setter
    def purge_unknown(self, value):
        self._config['purge_unknown'] = value

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, schema):
        if schema is None:
            self._schema = None
        elif self.is_child or isinstance(schema, DefinitionSchema):
            self._schema = schema
        else:
            self._schema = DefinitionSchema(self, schema)

    @property
    def transparent_schema_rules(self):
        return self._config.get('transparent_schema_rules', False)

    @transparent_schema_rules.setter
    def transparent_schema_rules(self, value):
        if isinstance(self._schema, DefinitionSchema):
            self._schema.regenerate_validation_schema()
            self._schema.update(dict())
        self._config['transparent_schema_rules'] = value

    # Document processing

    def __init_processing(self, document, schema=None):
        self._errors = errors.ErrorsList()
        self.document_error_tree = errors.DocumentErrorTree()
        self.schema_error_tree = errors.SchemaErrorTree()
        self.document = copy(document)

        if schema is not None:
            self.schema = DefinitionSchema(self, schema)
        elif self.schema is None:
            if isinstance(self.allow_unknown, Mapping):
                self.schema = {}
            else:
                raise SchemaError(errors.SCHEMA_ERROR_MISSING)
        if document is None:
            raise DocumentError(errors.DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise DocumentError(
                errors.DOCUMENT_FORMAT.format(document))
        self.root_document = self.root_document or document
        self.error_handler.start(self)

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
        self.__normalize_mapping(self.document, self.schema)
        self.error_handler.end(self)
        if self._errors:
            return None
        else:
            return self.document

    def __normalize_mapping(self, mapping, schema):
        self.__normalize_rename_fields(mapping, schema)
        if self.purge_unknown:
            self._normalize_purge_unknown(mapping, schema)
        self.__normalize_default_fields(mapping, schema)
        self._normalize_coerce(mapping, schema)
        self.__normalize_containers(mapping, schema)
        return mapping

    def _normalize_coerce(self, mapping, schema):
        """ {'anyof': [
                {'type': 'callable'},
                {'type': 'list',
                 'schema': {'oneof': [{'type': 'callable'},
                                      {'type': 'string'}]}},
                {'type': 'string'}
                ]} """

        error = errors.COERCION_FAILED
        for field in mapping:
            if field in schema and 'coerce' in schema[field]:
                mapping[field] = self.__normalize_coerce(
                    schema[field]['coerce'], field, mapping[field], error)
            elif isinstance(self.allow_unknown, Mapping) and \
                    'coerce' in self.allow_unknown:
                mapping[field] = self.__normalize_coerce(
                    self.allow_unknown['coerce'], field, mapping[field], error)

    def __normalize_coerce(self, processor, field, value, error):
        if isinstance(processor, _str_type):
            processor = self.__get_rule_handler('normalize_coerce', processor)
        elif isinstance(processor, Iterable):
            result = value
            for p in processor:
                result = self.__normalize_coerce(p, field, result, error)
                if errors.COERCION_FAILED in \
                    self.document_error_tree.fetch_errors_from(
                        self.document_path + (field,)):
                    break
            return result
        try:
            return processor(value)
        except Exception as e:
            self._error(field, error, str(e))
            return value

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
            if result[k] in mapping[field]:
                continue
            if result[k] in mapping[field]:
                warn("Normalizing keys of {path}: {key} already exists, "
                     "its value is replaced."
                     .format(path='.'.join(self.document_path + (field,)),
                             key=k))
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
        validator = self.__get_child_validator(
            document_crumb=field, schema_crumb=(field, 'schema'),
            schema=schema[field].get('schema', dict()),
            allow_unknown=schema[field].get('allow_unknown', self.allow_unknown),  # noqa
            purge_unknown=schema[field].get('purge_unknown', self.purge_unknown))  # noqa
        mapping[field] = validator.normalized(mapping[field])
        if validator._errors:
            self._error(validator._errors)

    def __normalize_sequence(self, field, mapping, schema):
        child_schema = dict(((k, schema[field]['schema'])
                             for k in range(len(mapping[field]))))
        validator = self.__get_child_validator(
            document_crumb=field, schema_crumb=(field, 'schema'),
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
        """ {'type': 'boolean'} """
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
                self._normalize_rename_handler(
                    mapping, {field: self.allow_unknown}, field)
        return mapping

    def _normalize_rename(self, mapping, schema, field):
        """ {'type': 'hashable'} """
        if 'rename' in schema[field]:
            mapping[schema[field]['rename']] = mapping[field]
            del mapping[field]

    def _normalize_rename_handler(self, mapping, schema, field):
        """ {'anyof': [
                {'type': 'callable'},
                {'type': 'list',
                 'schema': {'oneof': [{'type': 'callable'},
                                      {'type': 'string'}]}},
                {'type': 'string'}
                ]} """
        if 'rename_handler' not in schema[field]:
            return
        new_name = self.__normalize_coerce(
            schema[field]['rename_handler'], field, field,
            errors.RENAMING_FAILED)
        if new_name != field:
            mapping[new_name] = mapping[field]
            del mapping[field]

    def __normalize_default_fields(self, mapping, schema):
        def has_no_value(field):
            return field not in mapping or mapping[field] is None and \
                not schema[field].get('nullable', False)
        fields = list(filter(has_no_value, list(schema)))

        # process constant default values first
        for field in filter(lambda f: 'default' in schema[f], fields):
            self._normalize_default(mapping, schema, field)

        todo = list(filter(lambda f: 'default_setter' in schema[f], fields))
        known_states = set()
        while todo:
            field = todo.pop(0)
            try:
                self._normalize_default_setter(mapping, schema, field)
            except KeyError:
                # delay processing of this field as it may depend on
                # another default setter which is processed later
                todo.append(field)
            except Exception as e:
                self._error(field, errors.SETTING_DEFAULT_FAILED, str(e))
            self._watch_for_unresolvable_dependencies(todo, known_states)

    def _watch_for_unresolvable_dependencies(self, todo, known_states):
        """ Raises an error if the same todo list appears twice. """
        state = repr(todo)
        if state in known_states:
            for field in todo:
                msg = 'Circular/unresolvable dependencies for default setters.'
                self._error(field, errors.SETTING_DEFAULT_FAILED, msg)
                todo.remove(field)
        else:
            known_states.add(state)

    def _normalize_default(self, mapping, schema, field):
        """ {'nullable': True} """
        mapping[field] = schema[field]['default']

    def _normalize_default_setter(self, mapping, schema, field):
        """ {'anyof': [
                {'type': 'callable'},
                {'type': 'string'}
                ]} """
        if 'default_setter' in schema[field]:
            setter = schema[field]['default_setter']
            if isinstance(setter, _str_type):
                setter = self.__get_rule_handler('normalize_default_setter',
                                                 setter)
            mapping[field] = setter(mapping)

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
        self._unrequired_by_excludes = set()

        self.__init_processing(document, schema)
        if normalize:
            self.__normalize_mapping(self.document, self.schema)

        for field in self.document:
            if self.ignore_none_values and self.document[field] is None:
                continue
            definitions = self.schema.get(field)
            if definitions is not None:
                self.__validate_definitions(definitions, field)
            else:
                self.__validate_unknown_fields(field)

        if not self.update:
            self.__validate_required_fields(self.document)

        self.error_handler.end(self)

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
        warn('Validator.validate_update is deprecated. Use Validator.validate'
             '(update=True) instead.', DeprecationWarning)
        return self.validate(document, schema, update=True)

    def __validate_unknown_fields(self, field):
        if self.allow_unknown:
            value = self.document[field]
            if isinstance(self.allow_unknown, Mapping):
                # validate that unknown fields matches the schema
                # for unknown_fields
                schema_crumb = 'allow_unknown' if self.is_child \
                    else '__allow_unknown__'
                validator = self.__get_child_validator(
                    schema_crumb=schema_crumb,
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
            validator = self.__get_rule_handler('validate', rule)
            if validator:
                return validator(definitions.get(rule, None), field, value)

        value = self.document[field]

        """ _validate_-methods must return True to abort validation. """
        prior_rules = tuple((x for x in self.priority_validations
                             if x in definitions or
                             x in self.mandatory_validations))
        for rule in prior_rules:
            if validate_rule(rule):
                return

        rules = set(self.mandatory_validations)
        rules |= set(definitions.keys())
        rules -= set(prior_rules + ('allow_unknown', 'required'))
        rules -= set(self.normalization_rules)
        for rule in rules:
            validate_rule(rule)

    _validate_allow_unknown = dummy_for_rule_validation(
        """ {'type': ['boolean', 'dict'], 'validator': 'allow_unknown'} """)

    def _validate_allowed(self, allowed_values, field, value):
        """ {'type': 'list'} """
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
        """ {'type': ['dict', 'hashable', 'hashables']} """
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
        """ {'type': 'boolean'} """
        if isinstance(value, _str_type) and len(value) == 0 and not empty:
            self._error(field, errors.EMPTY_NOT_ALLOWED)

    def _validate_excludes(self, excludes, field, value):
        """ {'type': ['hashable', 'hashables']} """
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

    def _validate_forbidden(self, forbidden_values, field, value):
        """ {'type': 'list'} """
        if isinstance(value, _str_type):
            if value in forbidden_values:
                self._error(field, errors.FORBIDDEN_VALUE, value)
        elif isinstance(value, Sequence):
            forbidden = set(value) & set(forbidden_values)
            if forbidden:
                self._error(field, errors.FORBIDDEN_VALUES, list(forbidden))
        elif isinstance(value, int):
            if value in forbidden_values:
                self._error(field, errors.FORBIDDEN_VALUE, value)

    # TODO remove on next major release
    def _validate_items(self, items, field, value):
        """ {'type': ['list', 'dict'], 'validator': 'items'} """
        if isinstance(items, Mapping):
            self.__validate_items_schema(items, field, value)
        elif isinstance(items, Sequence) and not isinstance(items, _str_type):
            self.__validate_items_list(items, field, value)

    # TODO rename to _validate_items on next major release
    def __validate_items_list(self, items, field, values):
        """ {'type': 'list', 'validator': 'items'} """
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
    def __validate_items_schema(self, items, field, value):
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
        """ {'type': 'list', 'logical': 'anyof'} """
        self.__validate_logical('anyof', definitions, field, value)

    def _validate_allof(self, definitions, field, value):
        """ {'type': 'list', 'logical': 'allof'} """
        self.__validate_logical('allof', definitions, field, value)

    def _validate_noneof(self, definitions, field, value):
        """ {'type': 'list', 'logical': 'noneof'} """
        self.__validate_logical('noneof', definitions, field, value)

    def _validate_oneof(self, definitions, field, value):
        """ {'type': 'list', 'logical': 'oneof'} """
        self.__validate_logical('oneof', definitions, field, value)

    def _validate_max(self, max_value, field, value):
        try:
            if value > max_value:
                self._error(field, errors.MAX_VALUE)
        except TypeError:
            pass

    def _validate_min(self, min_value, field, value):
        try:
            if value < min_value:
                self._error(field, errors.MIN_VALUE)
        except TypeError:
            pass

    def _validate_maxlength(self, max_length, field, value):
        """ {'type': 'integer'} """
        if isinstance(value, Iterable) and len(value) > max_length:
                self._error(field, errors.MAX_LENGTH, len(value))

    def _validate_minlength(self, min_length, field, value):
        """ {'type': 'integer'} """
        if isinstance(value, Iterable) and len(value) < min_length:
                self._error(field, errors.MIN_LENGTH, len(value))

    def _validate_nullable(self, nullable, field, value):
        """ {'type': 'boolean'} """
        if value is None:
            if nullable:
                return True
            else:
                self._error(field, errors.NOT_NULLABLE)
                return True

    def _validate_propertyschema(self, schema, field, value):
        """ {'type': 'dict', 'validator': 'bulk_schema',
            'forbidden': ['rename', 'rename_handler']} """
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
        """ {'type': 'boolean'} """
        if readonly:
            self._error(field, errors.READONLY_FIELD)
            return True

    def _validate_regex(self, pattern, field, value):
        """ {'type': 'string'} """
        if not isinstance(value, _str_type):
            return
        if not pattern.endswith('$'):
            pattern += '$'
        re_obj = re.compile(pattern)
        if not re_obj.match(value):
            self._error(field, errors.REGEX_MISMATCH)

    _validate_required = dummy_for_rule_validation(""" {'type': 'boolean'} """)

    def __validate_required_fields(self, document):
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
        """ {'type': ['dict', 'list'], 'validator': 'schema'} """
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
        """ {'type': ['string', 'list']} """
        def call_type_validation(_type, value):
            # TODO refactor to a less complex code on next major release
            # validator = getattr(self, "_validate_type_" + _type)
            # return validator(field, value)

            prev_errors = len(self._errors)
            validator = getattr(self, "_validate_type_" +
                                _type.replace(' ', '_'))
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
            # for x in data_type:
            #     if call_type_validation(x, value):
            #         return
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
        if not isinstance(value, (_int_types, float)) \
                or isinstance(value, bool):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_set(self, field, value):
        if not isinstance(value, set):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_string(self, field, value):
        if not isinstance(value, _str_type):
            self._error(field, errors.BAD_TYPE)

    def _validate_validator(self, validator, field, value):
        """ {'anyof': [
                {'type': 'callable'},
                {'type': 'list',
                 'schema': {'oneof': [{'type': 'callable'},
                                      {'type': 'string'}]}},
                {'type': 'string'}
                ]} """
        if isinstance(validator, _str_type):
            validator = self.__get_rule_handler('validator', validator)
            validator(field, value)
        elif isinstance(validator, Iterable):
            for v in validator:
                self._validate_validator(v, field, value)
        else:
            validator(field, value, self._error)

    def _validate_valueschema(self, schema, field, value):
        """ {'type': 'dict', 'validator': 'bulk_schema',
            'forbidden': ['rename', 'rename_handler']} """
        schema_crumb = (field, 'valueschema')
        if isinstance(value, Mapping):
            validator = self.__get_child_validator(
                document_crumb=field, schema_crumb=schema_crumb,
                schema=dict((k, schema) for k in value))
            validator(value, normalize=False)
            if validator._errors:
                self._drop_nodes_from_errorpaths(validator._errors, [], [2])
                self._error(field, errors.VALUESCHEMA, validator._errors)
