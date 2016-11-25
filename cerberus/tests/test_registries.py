# -*- coding: utf-8 -*-

from cerberus import schema_registry, rules_set_registry, Validator
from cerberus.tests import assert_fail, assert_success


def test_schema_registry_simple():
    schema_registry.add('foo', {'bar': {'type': 'string'}})
    schema = {'a': {'schema': 'foo'},
              'b': {'schema': 'foo'}}
    document = {'a': {'bar': 'a'}, 'b': {'bar': 'b'}}
    assert_success(document, schema)


def test_top_level_reference():
    schema_registry.add('peng', {'foo': {'type': 'integer'}})
    document = {'foo': 42}
    assert_success(document, 'peng')


def test_rules_set_simple():
    rules_set_registry.add('foo', {'type': 'integer'})
    assert_success({'bar': 1}, {'bar': 'foo'})
    assert_fail({'bar': 'one'}, {'bar': 'foo'})


def test_allow_unknown_as_reference():
    rules_set_registry.add('foo', {'type': 'number'})
    v = Validator(allow_unknown='foo')
    assert_success({0: 1}, {}, v)
    assert_fail({0: 'one'}, {}, v)


def test_recursion():
    rules_set_registry.add('self',
                           {'type': 'dict', 'allow_unknown': 'self'})
    v = Validator(allow_unknown='self')
    assert_success({0: {1: {2: {}}}}, {}, v)


def test_references_remain_unresolved(validator):
    rules_set_registry.extend((('boolean', {'type': 'boolean'}),
                               ('booleans', {'valueschema': 'boolean'})))
    validator.schema = {'foo': 'booleans'}
    assert 'booleans' == validator.schema['foo']
    s = rules_set_registry._storage['booleans']['valueschema']
    assert 'boolean' == s


def test_rules_registry_with_anyof_type(validator):
    rules_set_registry.add('string_or_integer', {'anyof_type': ['string', 'integer']})
    schema = {'soi': 'string_or_integer'}
    assert_success({'soi': 'hello'}, schema)
