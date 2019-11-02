from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


@mark.parametrize('value', ('', (), {}, []))
def test_empty(value):
    field = 'test'
    document = {field: value}

    assert_success(schema={field: {}}, document=document)

    assert_success(schema={field: {"empty": True}}, document=document)

    assert_fail(
        schema={field: {"empty": False}},
        document=document,
        error=(field, (field, 'empty'), errors.EMPTY, False),
    )


def test_empty_skips_regex(validator):
    assert validator(
        document={'foo': ''}, schema={'foo': {'empty': True, 'regex': r'\d?\d\.\d\d'}}
    )
