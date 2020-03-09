from collections import abc, ChainMap
from typing import Hashable, MutableMapping, Sequence

from cerberus import errors
from cerberus.base import (
    normalize_schema,
    RulesSetRegistry,
    SchemaError,
    SchemaRegistry,
    TypeDefinition,
    UnconcernedValidator,
    normalize_rulesset,
)
from cerberus.platform import _GenericAlias
from cerberus.utils import schema_hash


class SchemaValidator(UnconcernedValidator):
    """ This validator provides mechanics to validate schemas passed to a Cerberus
        validator. """

    types_mapping = UnconcernedValidator.types_mapping.copy()
    types_mapping.update(
        {
            "container_but_not_string": TypeDefinition(
                "container_but_not_string", (abc.Container,), (str,)
            ),
            "generic_type_alias": TypeDefinition(
                "generic_type_alias", (_GenericAlias,), ()
            ),
        }
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("known_rules_set_refs", set())
        kwargs.setdefault("known_schema_refs", set())
        super().__init__(*args, **kwargs)

    @property
    def known_rules_set_refs(self):
        """ The encountered references to rules set registry items. """
        return self._config["known_rules_set_refs"]

    @property
    def known_schema_refs(self):
        """ The encountered references to schema registry items. """
        return self._config["known_schema_refs"]

    @property
    def target_validator(self):
        """ The validator whose schema is being validated. """
        return self._config['target_validator']

    def _check_with_dependencies(self, field, value):
        if isinstance(value, str):
            return
        elif isinstance(value, abc.Mapping):
            validator = self._get_child_validator(
                document_crumb=field,
                schema={'valuesrules': {'type': ('list',)}},
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
                self.known_rules_set_refs.add(value)
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

            self.known_schema_refs.add(value)
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

    # FIXME this rule seems to be called with very unexpected values
    # def _validate_type(self, data_type, field, value):
    #     assert isinstance(value, tuple), (self.schema_path, value)
    #     return super()._validate_type(data_type, field, value)


class ValidatedSchema(MutableMapping):
    """ A dict-subclass for caching of validated schemas. """

    def __init__(self, validator, schema=None):
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A definition-schema as ``dict``. Defaults to an empty
                       one.
        """
        self._repr = ("unvalidated schema: {}", schema)
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
        if not isinstance(schema, abc.Mapping):
            raise SchemaError(errors.SCHEMA_TYPE.format(schema))
        else:
            schema = normalize_schema(schema)

        self.validate(schema)
        self._repr = ("{}", schema)
        self.schema = schema

    def __delitem__(self, key):
        self.schema.pop(key)

    def __getitem__(self, item):
        return self.schema[item]

    def __iter__(self):
        return iter(self.schema)

    def __len__(self):
        return len(self.schema)

    def __repr__(self):
        # TODO include id
        return str(self)

    def __setitem__(self, key, value):
        value = normalize_rulesset(value)
        self.validate({key: value})
        self.schema[key] = value

    def __str__(self):
        return self._repr[0].format(self._repr[1])

    def copy(self):
        return self.__class__(self.validator, self.schema.copy())

    def update(self, schema):
        if not isinstance(schema, abc.Mapping):
            raise TypeError("Value must be of Mapping Type.")

        new_schema = ChainMap(schema, self.schema)
        self.validate(new_schema)
        self.schema = new_schema

    def regenerate_validation_schema(self):
        self.validation_schema = {
            'allow_unknown': False,
            'schema': self.validator.rules,
            'type': ('Mapping',),
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
                       according to the rules of the related Validator object.
        """
        if isinstance(schema, str):
            schema = self.validator.schema_registry.get(schema, schema)

        if schema is None:
            raise SchemaError(errors.SCHEMA_MISSING)

        resolved = {
            k: self.validator.rules_set_registry.get(v, v)
            for k, v in schema.items()
            if isinstance(v, str)
        }

        if not self.schema_validator(ChainMap(resolved, schema), normalize=False):
            raise SchemaError(self.schema_validator.errors)


__all__ = (RulesSetRegistry.__name__, SchemaRegistry.__name__)
