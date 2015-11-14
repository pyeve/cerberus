import logging

from .platform import _int_types, _str_type

log = logging.getLogger('cerberus')
depr_warnings_printed = {}


def compare_paths_lt(x, y):
    for i in range(min(len(x), len(y))):
        if isinstance(x[i], type(y[i])):
            if x[i] != y[i]:
                return x[i] < y[i]
        elif isinstance(x[i], _int_types):
            return True
        elif isinstance(y[i], _int_types):
            return False
    return len(x) < len(y)


def drop_item_from_tuple(t, i):
    return t[:i] + t[i+1:]


def quote_string(value):
    if isinstance(value, _str_type):
        return '"%s"' % value
    else:
        return value


def warn_deprecated(artifact, message):
    if not depr_warnings_printed.get(artifact):
        log.warn(message)
        depr_warnings_printed[artifact] = True
