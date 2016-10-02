from cerberus import schema_registry, rules_set_registry, Validator
from cerberus.tests import TestBase


class TestRegistries(TestBase):
    def test_schema_registry_simple(self):
        schema_registry.add('foo', {'bar': {'type': 'string'}})
        schema = {'a': {'schema': 'foo'},
                  'b': {'schema': 'foo'}}
        document = {'a': {'bar': 'a'}, 'b': {'bar': 'b'}}
        self.assertSuccess(document, schema)

    def test_top_level_reference(self):
        schema_registry.add('peng', {'foo': {'type': 'integer'}})
        document = {'foo': 42}
        self.assertSuccess(document, 'peng')

    def test_rules_set_simple(self):
        rules_set_registry.add('foo', {'type': 'integer'})
        self.assertSuccess({'bar': 1}, {'bar': 'foo'})
        self.assertFail({'bar': 'one'}, {'bar': 'foo'})

    def test_allow_unknown_as_reference(self):
        rules_set_registry.add('foo', {'type': 'number'})
        v = Validator(allow_unknown='foo')
        self.assertSuccess({0: 1}, {}, v)
        self.assertFail({0: 'one'}, {}, v)

    def test_recursion(self):
        rules_set_registry.add('self',
                               {'type': 'dict', 'allow_unknown': 'self'})
        v = Validator(allow_unknown='self')
        self.assertSuccess({0: {1: {2: {}}}}, {}, v)

    def test_references_remain_unresolved(self):
        rules_set_registry.extend((('boolean', {'type': 'boolean'}),
                                   ('booleans', {'valueschema': 'boolean'})))
        schema = {'foo': 'booleans'}
        self.validator.schema = schema
        assert 'booleans' == self.validator.schema['foo']
        s = rules_set_registry._storage['booleans']['valueschema']
        assert 'boolean' == s
