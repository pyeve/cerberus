from collections.abc import Callable, Mapping
from copy import copy
from typing import Dict, Hashable, MutableMapping, Sequence, Set

from cerberus import errors
from cerberus.base import (
    normalize_schema,
    rules_set_registry,
    RulesSetRegistry,
    SchemaError,
    SchemaRegistry,
    TypeDefinition,
    UnconcernedValidator,
    normalize_rulesset,
)
from cerberus.typing import SchemaDict


class SchemaValidator(UnconcernedValidator):
    """ This validator provides mechanics to validate schemas passed to a Cerberus
        validator. """

    types_mapping = UnconcernedValidator.types_mapping.copy()
    types_mapping.update(
        {
            'callable': TypeDefinition('callable', (Callable,), ()),  # type: ignore
            'hashable': TypeDefinition('hashable', (Hashable,), ()),
        }
    )

    @property
    def known_rules_set_refs(self):
        """ The encountered references to rules set registry items. """
        return self._config.get('known_rules_set_refs', ())

    @known_rules_set_refs.setter
    def known_rules_set_refs(self, value):
        self._config['known_rules_set_refs'] = value

    @property
    def known_schema_refs(self):
        """ The encountered references to schema registry items. """
        return self._config.get('known_schema_refs', ())

    @known_schema_refs.setter
    def known_schema_refs(self, value):
        self._config['known_schema_refs'] = value

    @property
    def target_validator(self):
        """ The validator whose schema is being validated. """
        return self._config['target_validator']

    def _check_with_dependencies(self, field, value):
        if isinstance(value, str):
            return
        elif isinstance(value, Mapping):
            validator = self._get_child_validator(
                document_crumb=field,
                schema={'valuesrules': {'type': 'list'}},
                allow_unknown=True,
            )
            if not validator(value, normalize=False):
                self._error(validator._errors)
        elif isinstance(value, Sequence):
            if not all(isinstance(x, Hashable) for x in value):
                path = self.document_path + (field,)
                self._error(path, 'All dependencies must be a hashable type.')

    def _check_with_items(self, field, value):
        self._check_with_schema(
            field, {i: rules_set for i, rules_set in enumerate(value)}
        )

    def _check_with_rulesset(self, field, value):
        # resolve schema registry reference
        if isinstance(value, str):
            if value in self.known_rules_set_refs:
                return
            else:
                self.known_rules_set_refs += (value,)
            definition = self.target_validator.rules_set_registry.get(value)
            if definition is None:
                self._error(field, "Rules set definition '{}' not found.".format(value))
                return
            else:
                value = definition

        _hash = (
            schema_hash({'turing': value}),
            schema_hash(self.target_validator.types_mapping),
        )
        if _hash in self.target_validator._valid_schemas:
            return

        validator = self._get_child_validator(
            document_crumb=field,
            allow_unknown=False,
            schema=self.target_validator.rules,
        )
        validator(value, normalize=False)
        if validator._errors:
            self._error(validator._errors)
        else:
            self.target_validator._valid_schemas.add(_hash)

    def _check_with_schema(self, field, value):
        if isinstance(value, str):
            if value in self.known_schema_refs:
                return

            self.known_schema_refs += (value,)
            definition = self.target_validator.schema_registry.get(value)
            if definition is None:
                path = self.document_path + (field,)
                self._error(path, "Schema definition '{}' not found.".format(value))
        else:
            definition = value

        _hash = (
            schema_hash(definition),
            schema_hash(self.target_validator.types_mapping),
        )
        if _hash in self.target_validator._valid_schemas:
            return

        validator = self._get_child_validator(
            document_crumb=field, schema=None, allow_unknown=self.root_allow_unknown
        )
        validator(self._expand_rules_set_refs(definition), normalize=False)
        if validator._errors:
            self._error(validator._errors)
        else:
            self.target_validator._valid_schemas.add(_hash)

    def _check_with_type_names(self, field, value):
        if value not in self.target_validator.types_mapping:
            self._error(field, 'Unsupported type name: {}'.format(value))

    def _expand_rules_set_refs(self, schema):
        result = {}
        for k, v in schema.items():
            if isinstance(v, str):
                result[k] = self.target_validator.rules_set_registry.get(v)
            else:
                result[k] = v
        return result

    def _validate_logical(self, rule, field, value):
        """ {'allowed': ('allof', 'anyof', 'noneof', 'oneof')} """
        if not isinstance(value, Sequence):
            self._error(field, errors.TYPE)
            return

        validator = self._get_child_validator(
            document_crumb=rule,
            allow_unknown=False,
            schema=self.target_validator.validation_rules,
        )

        for constraints in value:
            _hash = (
                schema_hash({'turing': constraints}),
                schema_hash(self.target_validator.types_mapping),
            )
            if _hash in self.target_validator._valid_schemas:
                continue

            validator(constraints, normalize=False)
            if validator._errors:
                self._error(validator._errors)
            else:
                self.target_validator._valid_schemas.add(_hash)


class ValidatedSchema(MutableMapping):
    """ A dict-subclass for caching of validated schemas. """

    def __init__(self, validator, schema=None):
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A definition-schema as ``dict``. Defaults to an empty
                       one.
        """
        if not isinstance(validator, UnconcernedValidator):
            raise RuntimeError('validator argument must be a Validator-' 'instance.')
        self.validator = validator
        self.regenerate_validation_schema()
        self.schema_validator = SchemaValidator(
            None,
            allow_unknown=self.validation_schema,
            error_handler=errors.SchemaErrorHandler,
            target_validator=validator,
        )

        if isinstance(schema, str):
            schema = validator.schema_registry.get(schema, schema)

        try:
            schema = dict(schema)  # type: ignore
        except Exception:
            raise SchemaError(errors.SCHEMA_TYPE.format(schema))

        schema = normalize_schema(schema)
        self.validate(schema)
        self.schema = schema

    def __delitem__(self, key):
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
        except ValueError:
            raise SchemaError("Schema has no field '{}' defined".format(key))
        except Exception:
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
        value = normalize_rulesset(value)
        self.validate({key: value})
        self.schema[key] = value

    def __str__(self):
        return str(self.schema)

    def copy(self):
        return self.__class__(self.validator, self.schema.copy())

    def update(self, schema):
        try:
            schema = normalize_schema(schema)
            _new_schema = self.schema.copy()
            _new_schema.update(schema)
            self.validate(_new_schema)
        except ValueError:
            raise SchemaError(errors.SCHEMA_TYPE.format(schema))
        except Exception as e:
            raise e
        else:
            self.schema = _new_schema

    def regenerate_validation_schema(self):
        self.validation_schema = {
            'allow_unknown': False,
            'schema': self.validator.rules,
            'type': 'dict',
        }

    def validate(self, schema=None):
        if schema is None:
            schema = self.schema
        _hash = (schema_hash(schema), schema_hash(self.validator.types_mapping))
        if _hash not in self.validator._valid_schemas:
            self._validate(schema)
            self.validator._valid_schemas.add(_hash)

    def _validate(self, schema):
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of this Validator object.
        """
        if isinstance(schema, str):
            schema = self.validator.schema_registry.get(schema, schema)

        if schema is None:
            raise SchemaError(errors.SCHEMA_MISSING)

        schema = copy(schema)
        for field in schema:
            if isinstance(schema[field], str):
                schema[field] = rules_set_registry.get(schema[field], schema[field])

        if not self.schema_validator(schema, normalize=False):
            raise SchemaError(self.schema_validator.errors)


def schema_hash(schema: SchemaDict) -> int:
    return hash(mapping_to_frozenset(schema))


def mapping_to_frozenset(schema: Mapping) -> frozenset:
    """ Be aware that this treats any sequence type with the equal members as
        equal. As it is used to identify equality of schemas, this can be
        considered okay as definitions are semantically equal regardless the
        container type. """
    schema_copy = {}  # type: Dict[Hashable, Hashable]
    for key, value in schema.items():
        if isinstance(value, Mapping):
            schema_copy[key] = mapping_to_frozenset(value)
        elif isinstance(value, Sequence):
            value = list(value)
            for i, item in enumerate(value):
                if isinstance(item, (ValidatedSchema, Dict)):
                    value[i] = mapping_to_frozenset(item)
            schema_copy[key] = tuple(value)
        elif isinstance(value, Set):
            schema_copy[key] = frozenset(value)
        elif isinstance(value, Hashable):
            schema_copy[key] = value
        else:
            raise TypeError("All schema contents must be hashable.")

    return frozenset(schema_copy.items())


__all__ = (RulesSetRegistry.__name__, SchemaRegistry.__name__)
