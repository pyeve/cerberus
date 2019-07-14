from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_schema(validator):
    field = 'a_dict'
    subschema_field = 'address'

    assert_success({field: {subschema_field: 'i live here', 'city': 'in my own town'}})

    assert_fail(
        schema={
            field: {
                'type': 'dict',
                'schema': {
                    subschema_field: {'type': 'string'},
                    'city': {'type': 'string', 'required': True},
                },
            }
        },
        document={field: {subschema_field: 34}},
        validator=validator,
        error=(
            field,
            (field, 'schema'),
            errors.SCHEMA,
            validator.schema['a_dict']['schema'],
        ),
        child_errors=[
            (
                (field, subschema_field),
                (field, 'schema', subschema_field, 'type'),
                errors.TYPE,
                ('string',),
            ),
            (
                (field, 'city'),
                (field, 'schema', 'city', 'required'),
                errors.REQUIRED_FIELD,
                True,
            ),
        ],
    )

    assert field in validator.errors
    assert subschema_field in validator.errors[field][-1]
    assert (
        errors.BasicErrorHandler.messages[errors.TYPE.code].format(
            constraint=('string',)
        )
        in validator.errors[field][-1][subschema_field]
    )
    assert 'city' in validator.errors[field][-1]
    assert (
        errors.BasicErrorHandler.messages[errors.REQUIRED_FIELD.code]
        in validator.errors[field][-1]['city']
    )


def test_options_passed_to_nested_validators(validator):
    validator.allow_unknown = True
    assert_success(
        schema={'sub_dict': {'type': 'dict', 'schema': {'foo': {'type': 'string'}}}},
        document={'sub_dict': {'foo': 'bar', 'unknown': True}},
        validator=validator,
    )
