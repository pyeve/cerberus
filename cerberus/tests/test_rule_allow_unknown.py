from cerberus import Validator
from cerberus.tests import assert_fail, assert_normalized, assert_success


def test_allow_unknown_in_schema():
    schema = {
        'field': {
            'type': 'dict',
            'allow_unknown': True,
            'schema': {'nested': {'type': 'string'}},
        }
    }
    document = {'field': {'nested': 'foo', 'arb1': 'bar', 'arb2': 42}}

    assert_success(document=document, schema=schema)

    schema['field']['allow_unknown'] = {'type': 'string'}
    assert_fail(document=document, schema=schema)


def test_allow_unknown_with_purge_unknown():
    validator = Validator(purge_unknown=True)
    schema = {'foo': {'type': 'dict', 'allow_unknown': True}}
    document = {'foo': {'bar': True}, 'bar': 'foo'}
    expected = {'foo': {'bar': True}}
    assert_normalized(document, expected, schema, validator)


def test_allow_unknown_with_purge_unknown_subdocument():
    validator = Validator(purge_unknown=True)
    schema = {
        'foo': {
            'type': 'dict',
            'schema': {'bar': {'type': 'string'}},
            'allow_unknown': True,
        }
    }
    document = {'foo': {'bar': 'baz', 'corge': False}, 'thud': 'xyzzy'}
    expected = {'foo': {'bar': 'baz', 'corge': False}}
    assert_normalized(document, expected, schema, validator)


def test_allow_unknown_without_schema():
    # https://github.com/pyeve/cerberus/issues/302
    v = Validator({'a': {'type': 'dict', 'allow_unknown': True}})
    v({'a': {}})
