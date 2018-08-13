#!/usr/bin/env python3

import importlib
from operator import attrgetter
from pathlib import Path
from pprint import pformat
from textwrap import indent
from types import SimpleNamespace


INCLUDES_DIR = Path(__file__).parent.resolve()
CERBERUS_DIR = INCLUDES_DIR.parent.parent / 'cerberus'


def load_module_members(name, path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    _module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(_module)
    return vars(_module)


errors_module = load_module_members('errors', CERBERUS_DIR / 'errors.py')
error_type = errors_module['ErrorDefinition']
error_definitions = []
for name, member in errors_module.items():
    if not isinstance(member, error_type):
        continue
    error_definition = SimpleNamespace(code=member.code, rule=member.rule)
    error_definition.name = name
    error_definitions.append(error_definition)
error_definitions.sort(key=attrgetter('code'))

with (INCLUDES_DIR / 'error-codes.rst').open('wt') as f:
    print(
        """
.. list-table::
   :header-rows: 1

   * - Code (dec.)
     - Code (hex.)
     - Name
     - Rule""".lstrip(
            '\n'
        ),
        file=f,
    )
    for error_definition in error_definitions:
        print(
            f"""
   * - {error_definition.code}
     - {hex(error_definition.code)}
     - {error_definition.name}
     - {error_definition.rule}""".lstrip(
                '\n'
            ),
            file=f,
        )

print('Generated table with ErrorDefinitions.')


validator_module = load_module_members('validator', CERBERUS_DIR / 'validator.py')
validator = validator_module['Validator']()
schema_validation_schema = pformat(
    validator.rules, width=68
)  # width seems w/o effect, use black?
with (INCLUDES_DIR / 'schema-validation-schema.rst').open('wt') as f:
    print(
        '.. code-block:: python\n\n', indent(schema_validation_schema, '    '), file=f
    )

print("Generated schema for a vanilla validator's, well, schema.")
