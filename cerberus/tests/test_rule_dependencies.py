from pytest import mark

from cerberus import errors, Validator
from cerberus.tests import assert_fail, assert_success


def test_dependencies_basic_error_handler_representation(validator):
    schema = {
        'field1': {'required': False},
        'field2': {'required': True, 'dependencies': {'field1': ['one', 'two']}},
    }
    validator.validate({'field2': 7}, schema=schema)
    expected_message = errors.BasicErrorHandler.messages[
        errors.DEPENDENCIES_FIELD_VALUE.code
    ].format(field='field2', constraint={'field1': ['one', 'two']})
    assert validator.errors == {'field2': [expected_message]}


def test_dependencies_errors():
    v = Validator(
        {
            'field1': {'required': False},
            'field2': {'required': True, 'dependencies': {'field1': ['one', 'two']}},
        }
    )
    assert_fail(
        {'field1': 'three', 'field2': 7},
        validator=v,
        error=(
            'field2',
            ('field2', 'dependencies'),
            errors.DEPENDENCIES_FIELD_VALUE,
            {'field1': ['one', 'two']},
            ({'field1': 'three'},),
        ),
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'a': 1, 'b': 'foo'}),
        (assert_success, {'a': 2, 'c': 'bar'}),
        (assert_fail, {'a': 1, 'c': 'foo'}),
        (assert_fail, {'a': 2, 'b': 'bar'}),
    ],
)
def test_dependencies_in_oneof(test_function, document):
    # https://github.com/pyeve/cerberus/issues/241
    test_function(
        schema={
            'a': {
                'type': 'integer',
                'oneof': [
                    {'allowed': [1], 'dependencies': 'b'},
                    {'allowed': [2], 'dependencies': 'c'},
                ],
            },
            'b': {},
            'c': {},
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': 'foobar', 'foo': 'bar', 'bar': 'foo'}),
        (assert_fail, {'field': 'foobar', 'foo': 'bar'}),
    ],
)
def test_dependencies_of_multiple_fields(test_function, document):
    test_function(
        schema={'field': {'dependencies': ['foo', 'bar']}, 'foo': {}, 'bar': {}},
        document=document,
    )


@mark.parametrize(
    "document",
    [
        {'field': 'foobar'},
        {'field': 'foobar', 'foo': 'bar'},
        {'field': 'foobar', 'bar': 'foo'},
        {'foo': 'bar', 'bar': 'foo'},
        {'foo': 'bar'},
    ],
)
def test_dependencies_of_multiple_fields_with_required_field_fails(document):
    assert_fail(
        schema={
            'field': {'required': True, 'dependencies': ['foo', 'bar']},
            'foo': {},
            'bar': {},
        },
        document=document,
    )


def test_dependencies_of_multiple_fields_with_required_field_succeeds():
    assert_success(
        schema={
            'field': {'required': False, 'dependencies': ['foo', 'bar']},
            'foo': {},
            'bar': {},
        },
        document={'foo': 'bar', 'bar': 'foo'},
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'foo': None, 'bar': 1}),
        (assert_success, {'foo': None}),
        (assert_fail, {'bar': 1}),
    ],
)
def test_dependencies_of_nullable_field_succeeds(test_function, document):
    # https://github.com/pyeve/cerberus/issues/305
    test_function(
        schema={'foo': {'nullable': True}, 'bar': {'dependencies': 'foo'}},
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': 'foobar', 'foo': 'bar'}),
        (assert_fail, {'field': 'foobar'}),
    ],
)
def test_dependencies_of_single_field(test_function, document):
    test_function(
        schema={'field': {'dependencies': 'foo'}, 'foo': {'type': 'string'}},
        document=document,
    )


def test_dependencies_relative_to_document_root():
    # https://github.com/pyeve/cerberus/issues/288
    subschema = {'version': {'dependencies': ('^repo',)}}
    schema = {'package': {'allow_unknown': True, 'schema': subschema}, 'repo': {}}

    assert_success({'repo': 'somewhere', 'package': {'version': 1}}, schema)

    assert_fail(
        {'package': {'repo': 'somewhere', 'version': 0}},
        schema,
        error=('package', ('package', 'schema'), errors.SCHEMA, subschema),
        child_errors=[
            (
                ('package', 'version'),
                ('package', 'schema', 'version', 'dependencies'),
                errors.DEPENDENCIES_FIELD,
                ('^repo',),
                ('^repo',),
            )
        ],
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'foo': None, 'bar': None}),
        (assert_success, {'foo': 1, 'bar': 1}),
        (assert_success, {'foo': None, 'bar': 1}),
        (assert_fail, {'foo': None}),
        (assert_fail, {'foo': 1}),
    ],
)
def test_dependencies_with_mutually_dependent_nullable_fields(test_function, document):
    # https://github.com/pyeve/cerberus/pull/306
    test_function(
        schema={
            'foo': {'dependencies': 'bar', 'nullable': True},
            'bar': {'dependencies': 'foo', 'nullable': True},
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'text': 'foo', 'deleted': False}),
        (assert_fail, {'text': 'foo', 'deleted': True}),
        (assert_fail, {'text': 'foo'}),
    ],
)
def test_dependencies_with_required_boolean_value(test_function, document):
    # https://github.com/pyeve/cerberus/issues/138
    test_function(
        schema={
            'deleted': {'type': 'boolean'},
            'text': {'dependencies': {'deleted': False}},
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'text': 'foo', 'deleted': False}),
        (assert_fail, {'text': 'foo', 'deleted': True}),
        (assert_fail, {'text': 'foo'}),
    ],
)
def test_dependencies_with_required_boolean_value_defined_in_list(
    test_function, document
):
    # https://github.com/pyeve/cerberus/issues/138
    test_function(
        schema={
            'deleted': {'type': 'boolean'},
            'text': {'dependencies': {'deleted': [False]}},
        },
        document=document,
    )


@mark.parametrize(
    "document",
    [
        {'field': 'foobar'},
        {'field': 'foobar', 'foo': 'foo'},
        {'field': 'foobar', 'bar': 'bar'},
        {'foo': 'foo', 'bar': 'bar'},
        {'foo': 'bar'},
    ],
)
def test_dependencies_with_required_rule_and_required_value_fails(document):
    assert_fail(
        schema={
            'field': {'required': True, 'dependencies': {'foo': 'foo', 'bar': 'bar'}},
            'foo': {},
            'bar': {},
        },
        document=document,
    )


def test_dependencies_with_required_rule_and_required_value_succeeds():
    schema = {
        'field': {'required': True, 'dependencies': {'foo': 'foo', 'bar': 'bar'}},
        'foo': {},
        'bar': {},
    }
    assert_success(
        document={'field': 'foobar', 'foo': 'foo', 'bar': 'bar'}, schema=schema
    )

    schema['field']['required'] = False
    assert_success(document={'foo': 'bar', 'bar': 'foo'}, schema=schema)


@mark.parametrize(
    "document",
    [
        {'field': 'foobar', 'foo': 'foo'},
        {'field': 'foobar', 'foo': 'bar'},
        {'field': 'foobar', 'bar': 'bar'},
        {'field': 'foobar', 'bar': 'foo'},
        {'field': 'foobar'},
    ],
)
def test_dependencies_with_required_value_fails(document):
    assert_fail(
        schema={
            'field': {'dependencies': {'foo': 'foo', 'bar': 'bar'}},
            'foo': {},
            'bar': {},
        },
        document=document,
    )


def test_dependencies_with_required_value_succeeds():
    assert_success(
        schema={
            'field': {'dependencies': {'foo': 'foo', 'bar': 'bar'}},
            'foo': {},
            'bar': {},
        },
        document={'field': 'foobar', 'foo': 'foo', 'bar': 'bar'},
    )


def test_nested_dependencies():
    schema = {
        'field': {'dependencies': ['a_dict.foo', 'a_dict.bar']},
        'a_dict': {'type': 'dict', 'schema': {'foo': {}, 'bar': {}}},
    }
    assert_success(
        document={'field': 'foobar', 'a_dict': {'foo': 'foo', 'bar': 'bar'}},
        schema=schema,
    )
    assert_fail(document={'field': 'foobar', 'a_dict': {}}, schema=schema)
    assert_fail(document={'field': 'foobar', 'a_dict': {'foo': 'foo'}}, schema=schema)


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': 'foobar', 'a_dict': {'foo': 'foo', 'bar': 'bar'}}),
        (assert_success, {'field': 'foobar', 'a_dict': {'foo': 'bar', 'bar': 'bar'}}),
        (assert_fail, {'field': 'foobar', 'a_dict': {}}),
        (assert_fail, {'field': 'foobar', 'a_dict': {'foo': 'foo', 'bar': 'foo'}}),
        (assert_fail, {'field': 'foobar', 'a_dict': {'bar': 'foo'}}),
        (assert_fail, {'field': 'foobar', 'a_dict': {'bar': 'bar'}}),
    ],
)
def test_nested_dependencies_with_required_values(test_function, document):
    test_function(
        schema={
            'field': {
                'dependencies': {'a_dict.foo': ['foo', 'bar'], 'a_dict.bar': 'bar'}
            },
            'a_dict': {'type': 'dict', 'schema': {'foo': {}, 'bar': {}}},
        },
        document=document,
    )
