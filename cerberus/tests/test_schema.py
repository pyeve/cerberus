from cerberus import Validator, errors, SchemaError
from cerberus.tests import TestBase


class TestDefinitionSchema(TestBase):
    def test_empty_schema(self):
        v = Validator()
        self.assertSchemaError(self.document, None, v,
                               errors.SCHEMA_ERROR_MISSING)

    def test_bad_schema_type(self):
        schema = "this string should really be dict"
        try:
            Validator(schema)
        except SchemaError as e:
            assert str(e) == \
                errors.SCHEMA_ERROR_DEFINITION_TYPE.format(schema)
        else:
            self.fail('SchemaError not raised')

        v = Validator()
        self.assertSchemaError(self.document, schema, v,
                               errors.SCHEMA_ERROR_DEFINITION_TYPE
                               .format(schema))

    def test_bad_schema_type_field(self):
        field = 'foo'
        schema = {field: {'schema': {'bar': {'type': 'strong'}}}}
        self.assertSchemaError(self.document, schema)

    def test_invalid_schema(self):
        self.assertSchemaError({}, {'foo': {'unknown': 'rule'}}, None,
                               "{'foo': [{'unknown': ['unknown rule']}]}")

    def test_unknown_rule(self):
        field = 'name'
        rule = 'unknown_rule'
        schema = {field: {rule: True, 'type': 'string'}}
        self.assertSchemaError(
            self.document, schema, None,
            str({field: [{rule: ['unknown rule']}]}))

    def test_unknown_type(self):
        field = 'name'
        value = 'catch_me'
        schema = {field: {'type': value}}
        self.assertSchemaError(
            self.document, schema, None,
            str({field: [{'type': ['unallowed value %s' % value]}]}))

    def test_bad_schema_definition(self):
        field = 'name'
        schema = {field: 'this should really be a dict'}
        self.assertSchemaError(self.document, schema, None,
                               str({field: ['must be of dict type']}))

    def bad_of_rules(self):
        schema = {'foo': {'anyof': {'type': 'string'}}}
        self.assertSchemaError({}, schema)

    def test_anyof_allof_schema_validate(self):
        # make sure schema with 'anyof' and 'allof' constraints are checked
        # correctly
        schema = {'doc': {'type': 'dict',
                          'anyof': [
                              {'schema': [{'param': {'type': 'number'}}]}]}}
        self.assertSchemaError({'doc': 'this is my document'}, schema)

        schema = {'doc': {'type': 'dict',
                          'allof': [
                              {'schema': [{'param': {'type': 'number'}}]}]}}
        self.assertSchemaError({'doc': 'this is my document'}, schema)

    def test_repr(self):
        v = Validator({'foo': {'type': 'string'}})
        assert repr(v.schema) == "{'foo': {'type': 'string'}}"

    def test_validated_schema_cache(self):
        v = Validator({'foozifix': {'coerce': int}})
        cache_size = len(v._valid_schemas)

        v = Validator({'foozifix': {'type': 'integer'}})
        cache_size += 1
        assert len(v._valid_schemas) == cache_size

        v = Validator({'foozifix': {'coerce': int}})
        assert len(v._valid_schemas) == cache_size

        max_cache_size = 200
        assert cache_size < max_cache_size, \
            "There's an unexpected high amount of cached valid " \
            "definition schemas. Unless you added further tests, " \
            "there are good chances that something is wrong. " \
            "If you added tests with new schemas, you can try to " \
            "adjust the variable `max_cache_size` according to " \
            "the added schemas."

    def test_expansion_in_nested_schema(self):
        schema = {'detroit':
                  {'schema': {'anyof_regex': ['^Aladdin', 'Sane$']}}}
        v = Validator(schema)
        assert v.schema['detroit']['schema'] == \
            {'anyof': [{'regex': '^Aladdin'}, {'regex': 'Sane$'}]}
