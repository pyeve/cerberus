#!/usr/bin/env python3

# TODO remove coercions of Path objects to strings when RTD builds on Python 3.6

import importlib.util
from operator import attrgetter
from pathlib import Path
from pprint import pformat
from types import SimpleNamespace


INCLUDES_DIR = Path(__file__).parent.resolve()
CERBERUS_DIR = INCLUDES_DIR.parent.parent / 'cerberus'


def load_module(name, path):
    module_spec = importlib.util.spec_from_file_location(name, str(path))
    _module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(_module)
    return _module


errors_module = load_module('errors', CERBERUS_DIR / 'errors.py')
error_type = vars(errors_module)['ErrorDefinition']
error_definitions = []
for name, member in vars(errors_module).items():
    if not isinstance(member, error_type) or member.rule is None:
        continue
    error_definition = SimpleNamespace(**member._asdict())
    error_definition.name = name
    error_definitions.append(error_definition)
error_definitions.sort(key=attrgetter('code'))

rows = []
for error_definition in error_definitions:
    rows.append((str(error_definition.code),
                 hex(error_definition.code),
                 error_definition.name,
                 error_definition.rule))
with open(str(INCLUDES_DIR / 'error-codes.rst'), 'wt') as f:
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


validator_module = load_module('validator', CERBERUS_DIR / 'validator.py')
validator = vars(validator_module)['Validator']()
schema_validation_schema = pformat(validator.rules)
with open(str(INCLUDES_DIR / 'schema-validation-schema.rst'), 'wt') as f:
    print('.. code-block:: python\n', file=f)
    for line in schema_validation_schema.split('\n'):
        print('    ' + line, file=f)
