#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from inspect import getmembers
import os
from pprint import pformat
import sys


DIR = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(DIR, '..', '..')))


import cerberus.errors
error_definitions = [x for x in getmembers(cerberus.errors)
                     if isinstance(x[1], cerberus.errors.ErrorDefinition)
                     and x[1].rule is not None]
error_definitions.sort(key=lambda x: x[1].code)
rows = []
for error_definition in error_definitions:
    rows.append((str(error_definition[1].code),
                hex(error_definition[1].code),
                error_definition[0],
                error_definition[1].rule))
with open (os.path.join(DIR, 'error-codes.rst'), 'wt') as f:
    print('.. list-table::\n'
          '   :header-rows: 1\n'
          '\n'
          '   * - Code (dec.)\n'
          '     - Code (hex.)\n'
          '     - Name\n'
          '     - Rule',
          file=f)
    for row in rows:
        print('   * - %s\n' % row[0] +
              '\n'.join(('     - ' + x for x in row[1:])),
              file=f)


from cerberus import Validator
schema_defintion_schema = pformat(Validator().rules)
with open(os.path.join(DIR, 'schema-validation-schema.rst'), 'wt') as f:
    print('.. code-block:: python\n', file=f)
    for line in schema_defintion_schema.split('\n'):
        print('    ' + line, file=f)
