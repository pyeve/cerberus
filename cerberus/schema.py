from __future__ import absolute_import

from collections import Callable, Hashable, Iterable, Mapping, MutableMapping
from copy import copy
import json

from cerberus import errors
from cerberus.platform import _str_type
from cerberus.utils import (cast_keys_to_strings, get_Validator_class,
                            validator_factory)


def schema_hash(schema):
    class Encoder(json.JSONEncoder):
        def default(self, o):
            return repr(o)

    return hash(json.dumps(cast_keys_to_strings(schema),
                           cls=Encoder, sort_keys=True))


class SchemaError(Exception):
    """ Raised when the validation schema is missing, has the wrong format or
        contains errors. """
    pass


class DefinitionSchema(MutableMapping):
    """ A dict-subclass for caching of validated schemas. """

    def __new__(cls, *args, **kwargs):
        if 'SchemaValidator' not in globals():
            global SchemaValidator
            SchemaValidator = validator_factory('SchemaValidator',
                                                SchemaValidatorMixin)
        return super(DefinitionSchema, cls).__new__(cls)

    def __init__(self, validator, schema={}):
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A definition-schema as ``dict``. Defaults to an empty
                      one.
        """
        if not isinstance(validator, get_Validator_class()):
            raise RuntimeError('validator argument must be a Validator-'
                               'instance.')
        self.validator = validator

        if isinstance(schema, _str_type):
            schema = validator.schema_registry.get(schema, schema)

        if not isinstance(schema, Mapping):
            try:
                schema = dict(schema)
            except Exception:
                raise SchemaError(
                    errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema))

        self.validation_schema = SchemaValidationSchema(validator)
        self.schema_validator = SchemaValidator(
            None, allow_unknown=self.validation_schema,
            error_handler=errors.SchemaErrorHandler,
            target_schema=schema, target_validator=validator)

        schema = self.expand(schema)
        self.validate(schema)
        self.schema = schema

    def __delitem__(self, key):
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
        except ValueError:
            raise SchemaError("Schema has no field '%s' defined" % key)
        except Exception as e:
            raise e
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
        value = self.expand({0: value})[0]
        self.validate({key: value})
        self.schema[key] = value

    def __str__(self):
        return str(self.schema)

    def expand(self, schema):
        try:
            schema = self._expand_logical_shortcuts(schema)
            schema = self._expand_subschemas(schema)
        except Exception:
            pass
        return schema

    def _expand_logical_shortcuts(self, schema):
        """ Expand agglutinated rules in a definition-schema.

        :param schema: The schema-definition to expand.
        :return: The expanded schema-definition.
        """
        def is_of_rule(x):
            return isinstance(x, _str_type) and \
                x.startswith(('allof_', 'anyof_', 'noneof_', 'oneof_'))

        for field in schema:
            for of_rule in (x for x in schema[field] if is_of_rule(x)):
                operator, rule = of_rule.split('_')
                schema[field].update({operator: []})
                for value in schema[field][of_rule]:
                    schema[field][operator].append({rule: value})
                del schema[field][of_rule]
        return schema

    def _expand_subschemas(self, schema):
        def has_schema_rule():
            return isinstance(schema[field], Mapping) and \
                'schema' in schema[field]

        def has_mapping_schema():
            """ Tries to determine heuristically if the schema-constraints are
                aimed to mappings. """
            try:
                return all(isinstance(x, Mapping) for x
                           in schema[field]['schema'].values())
            except TypeError:
                return False

        for field in schema:
            if not has_schema_rule():
                pass
            elif has_mapping_schema():
                schema[field]['schema'] = self.expand(schema[field]['schema'])
            else:  # assumes schema-constraints for a sequence
                schema[field]['schema'] = \
                    self.expand({0: schema[field]['schema']})[0]

            for rule in ('keyschema', 'valueschema'):
                if rule in schema[field]:
                    schema[field][rule] = \
                        self.expand({0: schema[field][rule]})[0]

            for rule in ('allof', 'anyof', 'items', 'noneof', 'oneof'):
                if rule in schema[field]:
                    new_rules_definition = []
                    for item in schema[field][rule]:
                        new_rules_definition.append(self.expand({0: item})[0])
                    schema[field][rule] = new_rules_definition
        return schema

    def update(self, schema):
        try:
            schema = self.expand(schema)
            _new_schema = self.schema.copy()
            _new_schema.update(schema)
            self.validate(_new_schema)
        except ValueError:
            raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_TYPE
                              .format(schema))
        except Exception as e:
            raise e
        else:
            self.schema = _new_schema

    def regenerate_validation_schema(self):
        self.validation_schema = SchemaValidationSchema(self.validator)

    def validate(self, schema=None):
        if schema is None:
            schema = self.schema
        _hash = schema_hash(schema)
        if _hash not in self.validator._valid_schemas:
            self._validate(schema)
            self.validator._valid_schemas.add(_hash)

    def _validate(self, schema):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.
        """
        if isinstance(schema, _str_type):
            schema = self.validator.schema_registry.get(schema, schema)

        if schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)

        schema = copy(schema)
        for field in schema:
            if isinstance(schema[field], _str_type):
                schema[field] = rules_set_registry.get(schema[field],
                                                       schema[field])

        if not self.schema_validator(schema, normalize=False):
            raise SchemaError(self.schema_validator.errors)


class UnvalidatedSchema(DefinitionSchema):
    def __init__(self, schema={}):
        if not isinstance(schema, Mapping):
            schema = dict(schema)
        self.schema = schema

    def validate(self, schema):
        pass


class SchemaValidationSchema(UnvalidatedSchema):
    def __init__(self, validator):
        self.schema = {'allow_unknown': False,
                       'schema': validator.rules,
                       'type': 'dict'}


class SchemaValidatorMixin:
    """ This validator is extended to validate schemas passed to a Cerberus
        validator. """
    @property
    def known_rules_set_refs(self):
        return self._config.get('known_rules_set_refs', ())

    @known_rules_set_refs.setter
    def known_rules_set_refs(self, value):
        self._config['known_rules_set_refs'] = value

    @property
    def known_schema_refs(self):
        return self._config.get('known_schema_refs', ())

    @known_schema_refs.setter
    def known_schema_refs(self, value):
        self._config['known_schema_refs'] = value

    @property
    def target_schema(self):
        """ The schema that is being validated. """
        return self._config['target_schema']

    @property
    def target_validator(self):
        """ The validator whose schema is being validated. """
        return self._config['target_validator']

    def _validate_logical(self, rule, field, value):
        """ {'allowed': ('allof', 'anyof', 'noneof', 'oneof')} """
        validator = self._get_child_validator(
            document_crumb=rule,
            schema=self.root_allow_unknown['schema'],
            allow_unknown=self.root_allow_unknown['allow_unknown']
        )

        for constraints in value:
            _hash = schema_hash({'turing': constraints})
            if _hash in self.target_validator._valid_schemas:
                continue

            validator(constraints, normalize=False)
            if validator._errors:
                self._error(validator._errors)
            else:
                self.target_validator._valid_schemas.add(_hash)

    def _validate_type_callable(self, value):
        if isinstance(value, Callable):
            return True

    def _validate_type_hashable(self, value):
        if isinstance(value, Hashable):
            return True

    def _validate_type_hashables(self, value):
        if self._validate_type_list(value):
            return all(self._validate_type_hashable(x) for x in value)

    def _validator_bulk_schema(self, field, value):
        if isinstance(value, _str_type):
            if value in self.known_rules_set_refs:
                return
            else:
                self.known_rules_set_refs += (value,)
            definition = self.target_validator.rules_set_registry.get(value)
            if definition is None:
                path = self.document_path + (field,)
                self._error(path, 'Rules set definition %s not found.' % value)
                return
            else:
                value = definition

        _hash = schema_hash({'turing': value})
        if _hash in self.target_validator._valid_schemas:
            return

        validator = self._get_child_validator(
            document_crumb=field,
            schema=self.root_allow_unknown['schema'],
            allow_unknown=self.root_allow_unknown['allow_unknown'])
        validator(value, normalize=False)
        if validator._errors:
            self._error(validator._errors)
        else:
            self.target_validator._valid_schemas.add(_hash)

    def _validator_handler(self, field, value):
        if isinstance(value, Callable):
            return
        if isinstance(value, _str_type):
            if value not in self.target_validator.validators + \
                    self.target_validator.coercers:
                self._error(field, '%s is no valid coercer' % value)
        elif isinstance(value, Iterable):
            for handler in value:
                self._validator_handler(field, handler)

    def _validator_items(self, field, value):
        for i, schema in enumerate(value):
            self._validator_bulk_schema((field, i), schema)

    def _validator_schema(self, field, value):
        if isinstance(value, _str_type):
            if value in self.known_schema_refs:
                return
            else:
                self.known_schema_refs += (value,)
            definition = self.target_validator.schema_registry.get(value)
            if definition is None:
                path = self.document_path + (field,)
                self._error(path, 'Schema definition %s not found.' % value)
                return
            else:
                value = definition

        _hash = schema_hash(value)
        if _hash in self.target_validator._valid_schemas:
            return

        validator = self._get_child_validator(
            document_crumb=field,
            schema=None, allow_unknown=self.root_allow_unknown)
        validator(value, normalize=False)
        if validator._errors:
            self._error(validator._errors)
        else:
            self.target_validator._valid_schemas.add(_hash)


####


class Registry:
    """ A registry to store and retrieve schemas and parts of it by a name
    that can be used in validation schemas.

    :param definitions: Optional, initial defintions.
    :type definitions: any :term:`mapping` """

    def __init__(self, definitions={}):
        self._storage = {}
        self.extend(definitions)

    def add(self, name, definition):
        """ Register a definition to the registry. Existing defintions are
        replaced silently.

        :param name: The name which can be used as reference in a validation
                     schema.
        :type name: :class:`str`
        :param definition: The definition.
        :type definition: any :term:`mapping` """
        self._storage[name] = definition

    def all(self):
        """ Returns a :class:`dict` with all registered definitions mapped to
        their name. """
        return self._storage

    def extend(self, definitions):
        """ Add several defintions at once. Existing defintions are
        replaced silently.

        :param definitions: The names and defintions.
        :type definitions: a :term:`mapping` or an :term:`iterable` with
                           two-value :class:`tuple` s """
        for name, definition in dict(definitions).items():
            self.add(name, definition)

    def clear(self):
        """ Purge all defintions in the registry. """
        self._storage.clear()

    def get(self, name, default=None):
        """ Retrieve a defintion from the registry.

        :param name: The reference that points to the defintion.
        :type name: :class:`str`
        :param default: Return value if the reference isn't registered. """
        return self._storage.get(name, default)

    def remove(self, *names):
        """ Unregister definitions from the registry.

        :param names: The names of the defintions that are to be
                      unregistered. """
        for name in names:
            self._storage.pop(name, None)


schema_registry, rules_set_registry = Registry(), Registry()
