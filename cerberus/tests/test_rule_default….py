from pytest import mark

from cerberus import errors, Validator
from cerberus.tests import assert_normalized


def must_not_be_called(*args, **kwargs):
    raise AssertionError('This shall not be called.')


@mark.parametrize(
    'default', ({'default': 'bar_value'}, {'default_setter': lambda doc: 'bar_value'})
)
def test_default_in_schema_with_missing_value(default):
    assert_normalized(
        schema={
            'thing': {
                'type': 'dict',
                'schema': {
                    'foo': {'type': 'string'},
                    'bar': {'type': 'string', **default},
                },
            }
        },
        document={'thing': {'foo': 'foo_value'}},
        expected={'thing': {'foo': 'foo_value', 'bar': 'bar_value'}},
    )


def test_default_setters_with_document_reference():
    assert_normalized(
        schema={
            'a': {'type': 'integer'},
            'b': {'type': 'integer', 'default_setter': lambda d: d['a'] + 1},
            'c': {'type': 'integer', 'default_setter': lambda d: d['b'] * 2},
            'd': {'type': 'integer', 'default_setter': lambda d: d['b'] + d['c']},
        },
        document={'a': 1},
        expected={'a': 1, 'b': 2, 'c': 4, 'd': 6},
    )


def test_default_setters_with_circular_document_reference(validator):
    validator(
        document={},
        schema={
            'a': {'default_setter': lambda d: d['b'] + 1},
            'b': {'default_setter': lambda d: d['a'] + 1},
        },
    )
    assert errors.SETTING_DEFAULT_FAILED in validator._errors


@mark.parametrize(
    'default', ({'default': 'bar_value'}, {'default_setter': must_not_be_called})
)
def test_default_with_existing_value(default):
    assert_normalized(
        schema={'foo': {'type': 'string'}, 'bar': {'type': 'string', **default}},
        document={'foo': 'foo_value', 'bar': 'non_default'},
        expected={'foo': 'foo_value', 'bar': 'non_default'},
    )


@mark.parametrize(
    'default', ({'default': 'bar_value'}, {'default_setter': lambda doc: 'bar_value'})
)
def test_default_with_missing_value(default):
    assert_normalized(
        schema={'foo': {'type': 'string'}, 'bar': {'type': 'string', **default}},
        document={'foo': 'foo_value'},
        expected={'foo': 'foo_value', 'bar': 'bar_value'},
    )


@mark.parametrize(
    'default', ({'default': 'bar_value'}, {'default_setter': lambda doc: 'bar_value'})
)
def test_default_with_non_nullable_field(default):
    assert_normalized(
        schema={
            'foo': {'type': 'string'},
            'bar': {'type': 'string', 'nullable': False, **default},
        },
        document={'foo': 'foo_value', 'bar': None},
        expected={'foo': 'foo_value', 'bar': 'bar_value'},
    )


def test_default_with_none_as_value_on_nullable_field():
    assert_normalized(
        schema={
            'foo': {'type': 'string'},
            'bar': {'type': 'string', 'nullable': True, 'default': None},
        },
        document={'foo': 'foo_value'},
        expected={'foo': 'foo_value', 'bar': None},
    )


@mark.parametrize(
    'default', ({'default': 'bar_value'}, {'default_setter': must_not_be_called})
)
def test_default_with_nullable_field(default):
    assert_normalized(
        schema={
            'foo': {'type': 'string'},
            'bar': {'type': 'string', 'nullable': True, **default},
        },
        document={'foo': 'foo_value', 'bar': None},
        expected={'foo': 'foo_value', 'bar': None},
    )


@mark.parametrize(
    "default",
    [{'default': 'cfg.yaml'}, {'default_setter': lambda document: 'cfg.yaml'}],
)
def test_default_in_schema_in_allow_unknown(default):
    validator = Validator(
        allow_unknown={
            'type': 'dict',
            'schema': {
                'cfg_path': {'type': 'string', **default},
                'package': {'type': 'string'},
            },
        }
    )
    assert_normalized(
        schema={'meta': {'type': 'dict'}, 'version': {'type': 'string'}},
        document={'version': '1.2.3', 'plugin_foo': {'package': 'foo'}},
        expected={
            'version': '1.2.3',
            'plugin_foo': {'package': 'foo', 'cfg_path': 'cfg.yaml'},
        },
        validator=validator,
    )
