from collections import Callable, Hashable, Iterable, Mapping, MutableMapping,\
    Sequence
import json
from warnings import warn

from . import errors
from .platform import _str_type
from .utils import cast_keys_to_strings, get_Validator_class, validator_factory


def schema_hash(schema, validator):
    class Encoder(json.JSONEncoder):
        def default(self, o):
            return repr(o)

    _hash = hash(json.dumps(cast_keys_to_strings(schema),
                            cls=Encoder, sort_keys=True))
    if validator.transparent_schema_rules:
        _hash *= -1

    return _hash


class SchemaError(Exception):
    """ Raised when the validation schema is missing, has the wrong format or
    contains errors.
    """
    pass


class DefinitionSchema(MutableMapping):
    """ A dict-subclass for caching of validated schemas.

        .. versionadded:: 0.10
    """

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

        if not isinstance(schema, Mapping):
            try:
                schema = dict(schema)
            except:
                raise SchemaError(
                    errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema))

        self.validation_schema = SchemaValidationSchema(validator)
        self.schema_validator = SchemaValidator(
            None, allow_unknown=self.validation_schema,
            error_handler=errors.SchemaErrorHandler,
            target_schema=schema, target_validator=validator)

        schema = expand_definition_schema(schema)
        self.validate(schema)
        self.schema = schema

    def __delitem__(self, key):
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
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
        self.validate({key: value})
        self.schema[key] = value

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

    def validate(self, schema=None):
        if schema is None:
            schema = self.schema
        _hash = schema_hash(schema, self.validator)
        if _hash not in self.validator._valid_schemas:
            self._validate(schema)
            self.validator._valid_schemas.add(_hash)

    def _validate(self, schema):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.

        .. versionadded:: 0.7.1
        """
        if schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)

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
    base = {'type': 'dict',
            'schema': {}}

    def __init__(self, validator):
        self.schema = self.base.copy()
        self.schema['schema'] = validator.rules
        self.schema['allow_unknown'] = validator.transparent_schema_rules


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
        validator = self._get_child_validator(
            document_crumb=rule,
            schema=self.root_allow_unknown['schema'],
            allow_unknown=self.root_allow_unknown['allow_unknown']
        )

        for constraints in value:
            _hash = schema_hash({'turing': constraints}, self.target_validator)
            if _hash in self.target_validator._valid_schemas:
                continue

            validator(constraints, normalize=False)
            if validator._errors:
                self._error(validator._errors)
            else:
                self.target_validator._valid_schemas.add(_hash)

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

    def _validator_bulk_schema(self, field, value):
        _hash = schema_hash({'turing': value}, self.target_validator)
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
            self._validator_schema(field, value)
        else:
            for i, schema in enumerate(value):
                self._validator_bulk_schema((field, i), schema)

    def _validator_schema(self, field, value):
        _hash = schema_hash(value, self.target_validator)
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

    def has_schema_rule(constraints):
        if not isinstance(constraints, Mapping):
            return False
        if 'schema' in constraints:
            return True
        else:
            return False

    def has_mapping_schema(constraints):
        """ Tries to determine heuristically if the schema-constraints are
            aimed to mappings. """
        for key in constraints['schema']:
            try:
                if not isinstance(constraints['schema'][key], Mapping):
                    return False
            except TypeError:
                return False
        return True

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

        if not has_schema_rule(schema[field]):
            pass
        elif has_mapping_schema(schema[field]):
            schema[field]['schema'] = \
                expand_definition_schema(schema[field]['schema'])
        else:  # assumes schema-constraints for a sequence
            schema[field]['schema'] = \
                expand_definition_schema({0: schema[field]['schema']})[0]

        for rule in ('propertyschema', 'valueschema'):
            if rule in schema[field]:
                schema[field][rule] = \
                    expand_definition_schema({0: schema[field][rule]})[0]

        for rule in ('allof', 'anyof', 'items', 'noneof', 'oneof'):
            # TODO remove instance-check at next major-release
            if rule in schema[field] and isinstance(schema[field][rule],
                                                    Sequence):
                new_rules_definition = []
                for item in schema[field][rule]:
                    new_rules_definition\
                        .append(expand_definition_schema({0: item})[0])
                schema[field][rule] = new_rules_definition

    return schema
