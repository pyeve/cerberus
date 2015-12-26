from collections import Callable, Hashable, Iterable, Mapping, MutableMapping,\
    Sequence
import json
from warnings import warn

from . import errors
from .platform import _str_type


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
                        warn("The 'items'-rule with a mapping as constraint is "
                             "deprecated. Use the 'schema'-rule instead.",
                             DeprecationWarning)
                        DefinitionSchema(self.validator, value)
                    else:
                        for item_schema in value:
                            DefinitionSchema(self.validator,
                                             {'schema': item_schema})
                elif constraint == 'dependencies':
                    self.__validate_dependencies_definition(field, value)
                elif constraint in ('coerce', 'rename_handler', 'validator'):
                    if not isinstance(value, (Callable, _str_type, Iterable)):
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
