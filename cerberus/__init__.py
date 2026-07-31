"""
Extensible validation for Python dictionaries.

:copyright: 2012-2023 by Nicola Iarocci.
:license: ISC, see LICENSE for more details.

Full documentation is available at https://python-cerberus.org/

"""

from cerberus.schema import rules_set_registry, schema_registry, SchemaError
from cerberus.utils import TypeDefinition
from cerberus.validator import DocumentError, Validator


__all__ = [
    DocumentError.__name__,
    SchemaError.__name__,
    TypeDefinition.__name__,
    Validator.__name__,
    "schema_registry",
    "rules_set_registry",
]
