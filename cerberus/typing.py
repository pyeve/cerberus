from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Hashable,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from cerberus.base import TypeDefinition  # noqa: F401
    from cerberus.errors import BaseErrorHandler  # noqa: F401
    from cerberus.schema import ValidatedSchema  # noqa: F401


FieldName = Hashable
Document = Mapping[FieldName, Any]
DocumentPath = Tuple[FieldName, ...]
ErrorHandlerConfig = Union[
    'BaseErrorHandler',
    Type['BaseErrorHandler'],
    Tuple[Type['BaseErrorHandler'], Mapping[str, Any]],
]
NoneType = type(None)
RulesSet = Mapping[str, Any]
SchemaDict = Mapping[FieldName, RulesSet]
Schema = Union['ValidatedSchema', SchemaDict]
AllowUnknown = Union[bool, RulesSet]
RegistryItem = TypeVar('RegistryItem', RulesSet, Schema)
RegistryItems = Union[Mapping[str, RegistryItem]]
TypesMapping = Dict[str, "TypeDefinition"]
