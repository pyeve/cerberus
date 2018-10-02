from collections.abc import ItemsView
from copy import copy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Hashable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

from cerberus import errors
from cerberus.base import (
    expand_schema,
    rules_set_registry,
    RulesSetRegistry,
    SchemaError,
    SchemaRegistry,
    TypeDefinition,
    TypesMapping,
    UnconcernedValidator,
)
from cerberus.typing import FieldName, RulesSet, Schema, SchemaDict


if TYPE_CHECKING:
    from cerberus.validator import Validator  # noqa: F401


class SchemaValidator(UnconcernedValidator):
    """ This validator provides mechanics to validate schemas passed to a Cerberus
        validator. """

    types_mapping = UnconcernedValidator.types_mapping.copy()
    types_mapping.update(
        {
            'callable': TypeDefinition('callable', (Callable,), ()),  # type: ignore
            'hashable': TypeDefinition('hashable', (Hashable,), ()),  # type: ignore
        }
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault('known_rules_set_refs', set())
        kwargs.setdefault('known_schema_refs', set())
        super().__init__(*args, **kwargs)

    @property
    def known_rules_set_refs(self) -> Set[str]:
        """ The encountered references to rules set registry items that have already
            been validated. """
        return self._config['known_rules_set_refs']

    @property
    def known_schema_refs(self) -> Set[str]:
        """ The encountered references to schema registry items that have already
            been validated. """
        return self._config['known_schema_refs']

    @property
    def target_validator(self) -> 'Validator':
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

    def _check_with_type(self, field, value):
        value = {value} if isinstance(value, str) else set(value)
        invalid_constraints = value - set(self.target_validator.types)
        if invalid_constraints:
            path = self.document_path + (field,)
            self._error(
                path, 'Unsupported types: {}'.format(', '.join(invalid_constraints))
            )

    def _expand_rules_set_refs(self, schema):
        result = {}
        for k, v in schema.items():
            if isinstance(v, str):
                result[k] = self.target_validator.rules_set_registry.get(v)
            else:
                result[k] = v
        return result

    def _validate_logical(self, rule: str, field: FieldName, value: Any) -> None:
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


# TODO in the future this could base on a structural type that will allow mypy to
#      identify its mapping-like capabilities, some currently ignored errors would
#      then cease. atm, it can't be derived from typing.Mapping b/c get's signature
#      conflicts with it.
class ValidatedSchema:
    """ A wrapper around a validated schema dictionary that mimics a dictionary
        interface. """

    def __init__(self, validator: 'Validator', schema: Dict) -> None:
        """
        :param validator: An instance of Validator-(sub-)class that uses this
                          schema.
        :param schema: A dictionary that defines a schema.
        """
        if not isinstance(validator, UnconcernedValidator):
            raise RuntimeError('validator argument must be a Validator-' 'instance.')
        self.validator = validator

        if isinstance(schema, str):
            schema = validator.schema_registry.get(schema, schema)

        if not isinstance(schema, Mapping):
            try:
                schema = dict(schema)
            except Exception:
                raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema))

        self.validation_schema = {}  # type: RulesSet
        self.regenerate_validation_schema()
        self.schema_validator = SchemaValidator(
            None,
            allow_unknown=self.validation_schema,
            error_handler=errors.SchemaErrorHandler,
            target_schema=schema,
            target_validator=validator,
        )

        expand_schema(schema)
        self.validate(schema)
        self.schema = schema

    def __delitem__(self, key: FieldName) -> None:
        _new_schema = self.schema.copy()
        try:
            del _new_schema[key]
        except ValueError:
            raise SchemaError("Schema has no field '{}' defined".format(key))
        except Exception:
            raise
        else:
            del self.schema[key]

    def __getitem__(self, item: FieldName) -> RulesSet:
        return self.schema[item]

    def __iter__(self) -> Iterator[FieldName]:
        return iter(self.schema)

    def __len__(self) -> int:
        return len(self.schema)

    def __repr__(self) -> str:
        return str(self)

    def __setitem__(self, key: FieldName, value: RulesSet) -> None:
        value = expand_schema({0: value})[0]
        self.validate({key: value})
        self.schema[key] = value

    def __str__(self) -> str:
        return str(self.schema)

    def copy(self) -> 'ValidatedSchema':
        return self.__class__(self.validator, self.schema.copy())

    def get(self, item: FieldName, default: RulesSet = None) -> Optional[RulesSet]:
        return self.schema.get(item, default)

    def items(self) -> ItemsView:
        return self.schema.items()

    def update(self, schema: SchemaDict) -> None:
        try:
            _new_schema = self.schema.copy()
            _new_schema.update(expand_schema(schema))  # type: ignore
            self.validate(_new_schema)
        except ValueError:
            raise SchemaError(errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema))
        except Exception as e:
            raise e
        else:
            self.schema = _new_schema

    def regenerate_validation_schema(self) -> None:
        self.validation_schema = {
            'allow_unknown': False,
            'schema': self.validator.rules,
            'type': 'dict',
        }

    def validate(self, schema: Optional[Schema] = None) -> None:
        """ Validates a schema that defines rules against supported rules.

        :param schema: The schema to be validated as a legal cerberus schema
                       according to the rules of the assigned Validator object.
                       Raises a :class:`~cerberus.base.SchemaError` when an invalid
                       schema is encountered. """
        if schema is None:
            schema = self.schema
        _hash = (schema_hash(schema), schema_hash(self.validator.types_mapping))
        if _hash not in self.validator._valid_schemas:
            self._validate(schema)
            self.validator._valid_schemas.add(_hash)

    def _validate(self, schema):
        if isinstance(schema, str):
            schema = self.validator.schema_registry.get(schema, schema)

        if schema is None:
            raise SchemaError(errors.SCHEMA_ERROR_MISSING)

        schema = copy(schema)
        for field in schema:
            if isinstance(schema[field], str):
                schema[field] = rules_set_registry.get(schema[field], schema[field])

        if not self.schema_validator(schema, normalize=False):
            raise SchemaError(self.schema_validator.errors)


def schema_hash(schema: Union[Schema, TypesMapping]) -> int:
    return hash(mapping_to_frozenset(schema))


def mapping_to_frozenset(schema: Union[Schema, TypesMapping]) -> frozenset:
    """ Be aware that this treats any sequence type with the equal members as
        equal. As it is used to identify equality of schemas, this can be
        considered okay as definitions are semantically equal regardless the
        container type. """

    aggregation = {}  # type: Dict[FieldName, Hashable]

    for key, value in schema.items():
        if isinstance(value, (ValidatedSchema, Dict)):
            aggregation[key] = mapping_to_frozenset(value)
        elif isinstance(value, Sequence):
            value = list(value)
            for i, item in enumerate(value):
                if isinstance(item, (ValidatedSchema, Dict)):
                    value[i] = mapping_to_frozenset(item)
            aggregation[key] = tuple(value)
        elif isinstance(value, Set):
            aggregation[key] = frozenset(value)
        else:
            aggregation[key] = value

    return frozenset(aggregation.items())


__all__ = (RulesSetRegistry.__name__, SchemaRegistry.__name__)
