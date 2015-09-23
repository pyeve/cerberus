"""
    Extensible validation for Python dictionaries.

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/

"""

from .cerberus import Validator, ValidationError, SchemaError

__version__ = "0.9.2"

__all__ = [
    Validator.__name__,
    ValidationError.__name__,
    SchemaError.__name__
]
