"""
    Extensible validation for Python dictionaries.

    :copyright: 2012 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/

"""

__version__ = "0.1.0"

from .cerberus import Validator, ValidationError, SchemaError


__all__ = [
    Validator.__name__,
    ValidationError.__name__,
    SchemaError.__name__
]
