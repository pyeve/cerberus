import re

from pytest import mark, raises

from cerberus import (
    errors,
    schema_registry,
    SchemaError,
    UnconcernedValidator,
    Validator,
)
from cerberus.tests import assert_schema_error, assert_success


def test_empty_schema():
    validator = Validator()
    with raises(SchemaError, match=errors.MISSING_SCHEMA):
        validator({}, schema=None)


def test_bad_schema_type(validator):
    schema = "this string should really be dict"
    msg = errors.SCHEMA_TYPE.format(schema)
    with raises(SchemaError, match=msg):
        validator.schema = schema


def test_bad_schema_type_field(validator):
    field = 'foo'
    schema = {field: {'schema': {'bar': {'type': 'strong'}}}}
    with raises(SchemaError):
        validator.schema = schema


def test_unknown_rule(validator):
    msg = "{'foo': [{'unknown': ['unknown rule']}]}"
    with raises(SchemaError, match=re.escape(msg)):
        validator.schema = {'foo': {'unknown': 'rule'}}


def test_unknown_type(validator):
    msg = str(
        {
            'foo': [
                {
                    'type': [
                        {
                            0: [
                                'none or more than one rule validate',
                                {
                                    'oneof definition 0': [
                                        'Unsupported type name: unknown'
                                    ],
                                    'oneof definition 1': [
                                        "must be one of these types: "
                                        "('type', 'generic_type_alias')"
                                    ],
                                },
                            ]
                        }
                    ]
                }
            ]
        }
    )

    with raises(SchemaError, match=re.escape(msg)):
        validator.schema = {'foo': {'type': 'unknown'}}


def test_bad_schema_definition(validator):
    field = 'name'
    msg = str({field: ["must be one of these types: ('Mapping',)"]})
    with raises(SchemaError, match=re.escape(msg)):
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
    assert repr(v.schema) == "{'foo': {'type': ('string',)}}"


def test_expansion_in_nested_schema():
    schema = {'detroit': {'itemsrules': {'anyof_regex': ['^Aladdin', 'Sane$']}}}
    v = Validator(schema)
    assert v.schema['detroit']['itemsrules'] == {
        'anyof': ({'regex': '^Aladdin'}, {'regex': 'Sane$'})
    }


def test_shortcut_expansion():
    def foo(field, value, error):
        pass

    def bar(field, value, error):
        pass

    validator = Validator({'field': {'anyof_check_with': [foo, bar]}})

    assert validator.schema == {
        'field': {'anyof': ({'check_with': foo}, {'check_with': bar})}
    }


def test_expansion_with_unvalidated_schema():
    validator = UnconcernedValidator(
        {"field": {'allof_regex': ['^Aladdin .*', '.* Sane$']}}
    )
    assert_success(document={"field": "Aladdin Sane"}, validator=validator)


def test_rulename_space_is_normalized():
    validator = Validator(
        schema={"field": {"default setter": lambda x: x, "type": "string"}}
    )
    assert "default_setter" in validator.schema["field"]


@mark.parametrize("rule", ("itemsrules", "keysrules", "valuesrules"))
def test_schema_normalization_does_not_abort(rule):
    schema_registry.clear()
    schema_registry.add(
        "schema_ref", {},
    )

    validator = Validator(
        schema={"field": {rule: {"type": "string"}, "schema": "schema_ref",},}  # noqa
    )
    assert validator.schema["field"][rule]["type"] == ("string",)
