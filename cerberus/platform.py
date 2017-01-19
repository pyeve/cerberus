""" Platform-dependent objects """

import sys


PYTHON_VERSION = float(sys.version_info[0]) + float(sys.version_info[1]) / 10


if PYTHON_VERSION < 3:
    _str_type = basestring  # noqa
    _int_types = (int, long)  # noqa
else:
    _str_type = str
    _int_types = (int,)
