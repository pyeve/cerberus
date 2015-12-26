"""
    Extensible validation for Python dictionaries.

    :copyright: 2012-2015 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://cerberus.readthedocs.org/

"""

from .cerberus import Validator, DocumentError
from .schema import SchemaError


__version__ = "0.10"

__all__ = [
    Validator.__name__,
    DocumentError.__name__,
    SchemaError.__name__
]
