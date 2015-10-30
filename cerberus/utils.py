import logging

from .platform import _str_type

log = logging.getLogger('cerberus')


def quote_string(value):
    if isinstance(value, _str_type):
        return '"%s"' % value
    else:
        return value


depr_warnings_printed = {}


def warn_deprecated(artifact, message):
    if not depr_warnings_printed.get(artifact):
        log.warn(message)
        depr_warnings_printed[artifact] = True
