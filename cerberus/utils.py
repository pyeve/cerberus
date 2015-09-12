import logging

log = logging.getLogger('cerberus')
depr_warnings_printed = {}


def warn_deprecated(artifact, message):
    if not depr_warnings_printed.get(artifact):
        log.warn(message)
        depr_warnings_printed[artifact] = True
