from collections import Callable, Hashable, Iterable, Mapping, MutableMapping,\
    Sequence
from copy import deepcopy
import json
from warnings import warn

from . import errors
from .platform import _str_type
from .utils import validator_fabric


class SchemaError(Exception):
    """ Raised when the validation schema is missing, has the wrong format or
    contains errors.
    """
    pass


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

    def __init__(self, validator, schema=dict()):
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A definition-schema as ``dict``. Defaults to an empty
                      one.
        """
        if not isinstance(schema, Mapping):
            try:
                schema = dict(schema)
            except:
                raise SchemaError(
                    errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema))

        schema = expand_definition_schema(schema)
        self.validator = validator
        self.schema = schema
        self.validation_schema = SchemaValidationSchema(validator)
        self.schema_validator = \
            validator_fabric('SchemaValidator', SchemaValidatorMixin)(
                UnvalidatedSchema(), error_handler=errors.SchemaErrorHandler,
                target_schema=schema, target_validator=validator)
        self.schema_validator.allow_unknown = self.validation_schema
        self.validate(self.schema)

    def __delitem__(self, key):
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
            self.validate(_new_schema)
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
            self.validate(_new_schema)
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
            self.validate(_new_schema)
        except ValueError:
            raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_TYPE
                              .format(schema))
        except:
            raise
        else:
            self.schema = _new_schema

    def regenerate_validation_schema(self):
        self.validation_schema = SchemaValidationSchema(self.validator)

    def validate(self, schema):
        _hash = hash(repr(type(self.validator)) +
                     str(self.validator.transparent_schema_rules) +
                     json.dumps(self.__cast_keys_to_strings(schema),
                                cls=self.Encoder, sort_keys=True))
        if _hash not in self.valid_schemas:
            self._validate(schema)
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

    def _validate(self, schema):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.

        .. versionadded:: 0.7.1
        """
        if schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)

        if not self.schema_validator(schema):
            raise SchemaError(self.schema_validator.errors)


class UnvalidatedSchema(DefinitionSchema):
    def __init__(self, schema=dict()):
        if not isinstance(schema, Mapping):
            schema = dict(schema)
        self.schema = schema

    def validate(self, schema):
        pass


class SchemaValidationSchema(UnvalidatedSchema):
    base = {'type': 'dict',
            'allow_unknown': False,
            'schema': {}}

    def __init__(self, validator):
        self.schema = self.base.copy()
        self.schema['schema'].update(validator.rules)
        if validator.transparent_schema_rules:
            self.schema['allow_unknown'] = True


class SchemaValidatorMixin:
    @property
    def target_schema(self):
        """ The schema that is being validated. """
        return self._config['target_schema']

    @property
    def target_validator(self):
        """ The validator whose schema is being validated. """
        return self._config['target_validator']

    def _validate_logical(self, rule, none, value):
        field = tuple(self.target_schema.keys())[0]
        for of_constraint in value:
            schema = deepcopy(self.target_schema)
            del schema[field][rule]
            schema[field].update(of_constraint)
            DefinitionSchema(self.target_validator, schema)

    def _validate_type_callable(self, field, value):
        if not isinstance(value, Callable):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_hashable(self, field, value):
        if not isinstance(value, Hashable):
            self._error(field, errors.BAD_TYPE)

    def _validate_type_hashables(self, field, value):
        self._validate_type_list(field, value)
        for item in value:
            self._validate_type_hashable(field, item)

    def _validator_allow_unknown(self, field, value):
        if not isinstance(value, bool):
            DefinitionSchema(self.target_validator, {field: value})

    def _validator_bulk_schema(self, field, value):
        DefinitionSchema(self.target_validator, {field: value})

    def _validator_handler(self, field, value):
        if isinstance(value, Callable):
            return
        if isinstance(value, _str_type):
            if value not in self.target_validator.validators and \
                    value not in self.target_validator.coercers:
                self._error(field, '%s is no valid coercer' % value)
        elif isinstance(value, Iterable):
            for handler in value:
                self._validator_handler(field, handler)

    def _validator_items(self, field, value):
        if isinstance(value, Mapping):
            # TODO remove on next major release
            warn("The 'items'-rule with a mapping as constraint is "
                 "deprecated. Use the 'schema'-rule instead.",
                 DeprecationWarning)
            DefinitionSchema(self.target_validator, value)
        else:
            for item_schema in value:
                DefinitionSchema(self.target_validator,
                                 {0: item_schema})

    def _validator_schema(self, field, value):
        try:
            DefinitionSchema(self.target_validator, value)
        except SchemaError:
            self._validator_bulk_schema(field, value)


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
            warn("The 'keyschema'-rule is deprecated. Use 'valueschema' instead.",  # noqa
                 DeprecationWarning)
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
