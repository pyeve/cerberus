from random import choice
from string import ascii_lowercase

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_minlength_and_maxlength_with_list(schema):
    field = 'a_list_length'
    min_length = schema[field]['minlength']
    max_length = schema[field]['maxlength']

    assert_fail(
        {field: [1] * (min_length - 1)},
        error=(
            field,
            (field, 'minlength'),
            errors.MIN_LENGTH,
            min_length,
            (min_length - 1,),
        ),
    )

    for i in range(min_length, max_length):
        assert_success({field: [1] * i})

    assert_fail(
        {field: [1] * (max_length + 1)},
        error=(
            field,
            (field, 'maxlength'),
            errors.MAX_LENGTH,
            max_length,
            (max_length + 1,),
        ),
    )


def test_maxlength_fails(schema):
    field = 'a_string'
    max_length = schema[field]['maxlength']
    value = "".join(choice(ascii_lowercase) for i in range(max_length + 1))
    assert_fail(
        document={field: value},
        error=(
            field,
            (field, 'maxlength'),
            errors.MAX_LENGTH,
            max_length,
            (len(value),),
        ),
    )


def test_maxlength_with_bytestring_fails(schema):
    field = 'a_bytestring'
    max_length = schema[field]['maxlength']
    value = b'\x00' * (max_length + 1)
    assert_fail(
        document={field: value},
        error=(
            field,
            (field, 'maxlength'),
            errors.MAX_LENGTH,
            max_length,
            (len(value),),
        ),
    )


def test_minlength_fails(schema):
    field = 'a_string'
    min_length = schema[field]['minlength']
    value = "".join(choice(ascii_lowercase) for i in range(min_length - 1))
    assert_fail(
        document={field: value},
        error=(
            field,
            (field, 'minlength'),
            errors.MIN_LENGTH,
            min_length,
            (len(value),),
        ),
    )


def test_minlength_with_bytestring_fails(schema):
    field = 'a_bytestring'
    min_length = schema[field]['minlength']
    value = b'\x00' * (min_length - 1)
    assert_fail(
        document={field: value},
        error=(
            field,
            (field, 'minlength'),
            errors.MIN_LENGTH,
            min_length,
            (len(value),),
        ),
    )


def test_minlength_with_dict():
    schema = {'dict': {'minlength': 1}}
    assert_fail(document={'dict': {}}, schema=schema)
    assert_success(document={'dict': {'foo': 'bar'}}, schema=schema)
