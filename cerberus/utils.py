from __future__ import print_function
import logging


class PrintLogger:
    @staticmethod
    def warn(message):
        print('WARNING cerberus: ' + message)


try:
    log = logging.getLogger('cerberus')
except:
    log = PrintLogger


depr_warnings_printed = {}


def warn_deprecated(artifact, message):
    if not depr_warnings_printed.get(artifact):
        log.warn(message)
        depr_warnings_printed[artifact] = True
