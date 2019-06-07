import re

import pytest

from cerberus import Validator, errors, SchemaError, UnconcernedValidator
from cerberus.tests import assert_schema_error, assert_success


def test_empty_schema():
    validator = Validator()
    with pytest.raises(SchemaError, match=errors.MISSING_SCHEMA):
        validator({}, schema=None)


def test_bad_schema_type(validator):
    schema = "this string should really be dict"
    msg = errors.SCHEMA_TYPE.format(schema)
    with pytest.raises(SchemaError, match=msg):
        validator.schema = schema


def test_bad_schema_type_field(validator):
    field = 'foo'
    schema = {field: {'schema': {'bar': {'type': 'strong'}}}}
    with pytest.raises(SchemaError):
        validator.schema = schema


def test_unknown_rule(validator):
    msg = "{'foo': [{'unknown': ['unknown rule']}]}"
    with pytest.raises(SchemaError, match=re.escape(msg)):
        validator.schema = {'foo': {'unknown': 'rule'}}


def test_unknown_type(validator):
    msg = str({'foo': [{'type': ['Unsupported types: unknown']}]})
    with pytest.raises(SchemaError, match=re.escape(msg)):
        validator.schema = {'foo': {'type': 'unknown'}}


def test_bad_schema_definition(validator):
    field = 'name'
    msg = str({field: ['must be of dict type']})
    with pytest.raises(SchemaError, match=re.escape(msg)):
        validator.schema = {field: 'this should really be a dict'}


def test_bad_of_rules():
    schema = {'foo': {'anyof': {'type': 'string'}}}
    assert_schema_error({}, schema)


def test_normalization_rules_are_invalid_in_of_rules():
    schema = {0: {'anyof': [{'coerce': lambda x: x}]}}
    assert_schema_error({}, schema)


def test_anyof_allof_schema_validate():
    # make sure schema with 'anyof' and 'allof' constraints are checked
    # correctly
    schema = {
        'doc': {'type': 'dict', 'anyof': [{'schema': [{'param': {'type': 'number'}}]}]}
    }
    assert_schema_error({'doc': 'this is my document'}, schema)

    schema = {
        'doc': {'type': 'dict', 'allof': [{'schema': [{'param': {'type': 'number'}}]}]}
    }
    assert_schema_error({'doc': 'this is my document'}, schema)


def test_repr():
    v = Validator({'foo': {'type': 'string'}})
    assert repr(v.schema) == "{'foo': {'type': 'string'}}"


def test_validated_schema_cache():
    v = Validator({'foozifix': {'coerce': int}})
    cache_size = len(v._valid_schemas)

    v = Validator({'foozifix': {'type': 'integer'}})
    cache_size += 1
    assert len(v._valid_schemas) == cache_size

    v = Validator({'foozifix': {'coerce': int}})
    assert len(v._valid_schemas) == cache_size

    max_cache_size = 162
    assert cache_size <= max_cache_size, (
        "There's an unexpected high amount (%s) of cached valid "
        "definition schemas. Unless you added further tests, "
        "there are good chances that something is wrong. "
        "If you added tests with new schemas, you can try to "
        "adjust the variable `max_cache_size` according to "
        "the added schemas." % cache_size
    )


def test_expansion_in_nested_schema():
    schema = {'detroit': {'itemsrules': {'anyof_regex': ['^Aladdin', 'Sane$']}}}
    v = Validator(schema)
    assert v.schema['detroit']['itemsrules'] == {
        'anyof': [{'regex': '^Aladdin'}, {'regex': 'Sane$'}]
    }


def test_anyof_check_with():
    def foo(field, value, error):
        pass

    def bar(field, value, error):
        pass

    schema = {'field': {'anyof_check_with': [foo, bar]}}
    validator = Validator(schema)

    assert validator.schema == {
        'field': {'anyof': [{'check_with': foo}, {'check_with': bar}]}
    }


def test_expansion_with_unvalidated_schema():
    validator = UnconcernedValidator(
        {"field": {'allof_regex': ['^Aladdin .*', '.* Sane$']}}
    )
    assert_success(document={"field": "Aladdin Sane"}, validator=validator)
