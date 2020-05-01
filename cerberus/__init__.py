"""
    Extensible validation for Python dictionaries.

    :copyright: 2012-2016 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org/

"""

from pkg_resources import get_distribution, DistributionNotFound
from typing import Dict, Optional, Tuple, Union

from cerberus.base import (
    rules_set_registry,
    schema_registry,
    DocumentError,
    TypeDefinition,
    UnconcernedValidator,
)
from cerberus.schema import SchemaError
from cerberus.validator import Validator


try:
    __version__ = get_distribution("Cerberus").version
except DistributionNotFound:
    __version__ = "unknown"


def validator_factory(
    name: str,
    bases: Union[type, Tuple[type], None] = None,
    namespace: Optional[Dict] = None,
    validated_schema: bool = True,
) -> type:
    """ Dynamically create a :class:`~cerberus.Validator` subclass.
        Docstrings of mixin-classes will be added to the resulting
        class' one if ``__doc__`` is not in :obj:`namespace`.

    :param name: The name of the new class.
    :param bases: Class(es) with additional and overriding attributes.
    :param namespace: Attributes for the new class.
    :param validated_schema: Indicates that schemas that are provided to the validator
                             are to be validated.
    :return: The created class.
    """

    validator_class = Validator if validated_schema else UnconcernedValidator

    if namespace is None:
        namespace = {}

    if bases is None:
        computed_bases = (validator_class,)
    elif isinstance(bases, tuple) and validator_class not in bases:
        computed_bases = bases + (validator_class,)  # type: ignore
    else:
        computed_bases = (bases, validator_class)  # type: ignore

    docstrings = [x.__doc__ for x in computed_bases if x.__doc__]
    if len(docstrings) > 1 and '__doc__' not in namespace:
        namespace.update({'__doc__': '\n'.join(docstrings)})

    return type(name, computed_bases, namespace)


__all__ = [
    DocumentError.__name__,
    SchemaError.__name__,
    TypeDefinition.__name__,
    UnconcernedValidator.__name__,
    Validator.__name__,
    "__version__",
    'schema_registry',
    'rules_set_registry',
    validator_factory.__name__,
]
