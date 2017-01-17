""" Platform-dependent objects """

import copy
import sys
from functools import wraps


PYTHON_VERSION = float(sys.version_info[0]) + float(sys.version_info[1]) / 10


if PYTHON_VERSION < 3:
    _str_type = basestring  # noqa
    _int_types = (int, long)  # noqa
else:
    _str_type = str
    _int_types = (int,)


def py2_error_unicode_fix(f):
    """Cerberus error messages expect regular binary strings.
    If unicode is used in schema message can't be printed.

    This decorator ensures that if legacy Python is used unicode
    strings are encoded before passing to a function.
    """
    @wraps(f)
    def wrapped(obj, error):
        if PYTHON_VERSION < 3:
            error = copy.copy(error)
            error.document_path = _encode(error.document_path)
            error.schema_path = _encode(error.schema_path)
            error.constraint = _encode(error.constraint)
            error.value = _encode(error.value)
            error.info = _encode(error.info)

        return f(obj, error)
    return wrapped


def _encode(value):
    """Helper encoding unicode strings into binary utf-8"""
    if isinstance(value, unicode):
        return value.encode('utf-8')
    return value
