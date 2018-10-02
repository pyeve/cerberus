from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Hashable,
    Iterable,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from cerberus.errors import BaseErrorHandler  # noqa: F401
    from cerberus.schema import ValidatedSchema  # noqa: F401


FieldName = Hashable
Document = Mapping[FieldName, Any]
DocumentPath = Tuple[FieldName, ...]
ErrorHandlerConfig = Union[
    'BaseErrorHandler',
    Type['BaseErrorHandler'],
    Tuple[Type['BaseErrorHandler'], Dict[str, Any]],
]
Handler = Union[str, Callable, Iterable[Union[str, Callable]]]
RulesSet = Dict[str, Any]
SchemaDict = Dict[FieldName, RulesSet]
Schema = Union['ValidatedSchema', SchemaDict]
AllowUnknown = Union[bool, Schema]
RegistryItem = TypeVar('RegistryItem', RulesSet, Schema)
RegistryItems = Union[Dict[str, RegistryItem]]
