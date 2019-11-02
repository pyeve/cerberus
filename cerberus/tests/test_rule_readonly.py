from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_nested_readonly_with_defaults():
    schema = {
        'some_field': {
            'type': 'dict',
            'schema': {
                'created': {'type': 'string', 'readonly': True, 'default': 'today'},
                'modified': {
                    'type': 'string',
                    'readonly': True,
                    'default_setter': lambda d: d['created'],
                },
            },
        }
    }

    assert_success(document={'some_field': {}}, schema=schema)

    expected_errors = [
        (
            ('some_field', 'created'),
            ('some_field', 'schema', 'created', 'readonly'),
            errors.READONLY_FIELD,
            schema['some_field']['schema']['created']['readonly'],
        ),
        (
            ('some_field', 'modified'),
            ('some_field', 'schema', 'modified', 'readonly'),
            errors.READONLY_FIELD,
            schema['some_field']['schema']['modified']['readonly'],
        ),
    ]

    assert_fail(
        document={'some_field': {'created': 'tomorrow', 'modified': 'now'}},
        schema=schema,
        errors=expected_errors,
    )
    assert_fail(
        document={'some_field': {'created': 'today', 'modified': 'today'}},
        schema=schema,
        errors=expected_errors,
    )


def test_readonly():
    field = 'a_readonly_string'
    assert_fail(
        {field: 'update me if you can'},
        error=(field, (field, 'readonly'), errors.READONLY_FIELD, True),
    )


def test_readonly_skips_further_validation(validator):
    # test that readonly rule is checked before any other rule, and blocks.
    # https://github.com/pyeve/cerberus/issues/63
    field = "a_readonly_number"
    assert_fail(
        schema={field: {'type': 'integer', 'readonly': True, 'max': 1}},
        document={field: 2},
        errors=[(field, (field, "readonly"), errors.READONLY_FIELD, True)],
    )


def test_readonly_with_defaults():
    schema = {
        'created': {'type': 'string', 'readonly': True, 'default': 'today'},
        'modified': {
            'type': 'string',
            'readonly': True,
            'default_setter': lambda d: d['created'],
        },
    }

    assert_success(document={}, schema=schema)

    expected_errors = [
        (
            'created',
            ('created', 'readonly'),
            errors.READONLY_FIELD,
            schema['created']['readonly'],
        ),
        (
            'modified',
            ('modified', 'readonly'),
            errors.READONLY_FIELD,
            schema['modified']['readonly'],
        ),
    ]

    assert_fail(
        document={'created': 'tomorrow', 'modified': 'today'},
        schema=schema,
        errors=expected_errors,
    )
    assert_fail(
        document={'created': 'today', 'modified': 'today'},
        schema=schema,
        errors=expected_errors,
    )


def test_repeated_readonly(validator):
    # https://github.com/pyeve/cerberus/issues/311
    validator.schema = {'id': {'readonly': True}}
    assert_fail({'id': 0}, validator=validator)
    assert_fail({'id': 0}, validator=validator)
