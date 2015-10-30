""" Platform-dependent objects """

import sys


if sys.version_info[0] == 3:
    _str_type = str
    _int_types = (int,)
else:
    _str_type = basestring  # noqa
    _int_types = (int, long)  # noqa
