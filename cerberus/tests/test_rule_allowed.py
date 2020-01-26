from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_allowed_with_integer_value_fail():
    field = 'a_restricted_integer'
    value = 2
    assert_fail(
        {field: value},
        error=(field, (field, 'allowed'), errors.UNALLOWED_VALUE, [-1, 0, 1], value),
    )


def test_allowed_with_integer_value_succeed():
    assert_success({'a_restricted_integer': -1})


def test_allowed_with_list_value():
    field = 'an_array'
    value = ['agent', 'client', 'profit']
    assert_fail(
        {field: value},
        error=(
            field,
            (field, 'allowed'),
            errors.UNALLOWED_VALUES,
            ['agent', 'client', 'vendor'],
            (('profit',),),
        ),
    )


def test_allowed_with_set_value():
    assert_success({'an_array_from_set': ['agent', 'client']})


def test_allowed_with_string_value():
    field = 'a_restricted_string'
    value = 'profit'
    assert_fail(
        {field: value},
        error=(
            field,
            (field, 'allowed'),
            errors.UNALLOWED_VALUE,
            ['agent', 'client', 'vendor'],
            value,
        ),
    )


def test_allowed_with_unicode_chars():
    # http://github.com/pyeve/cerberus/issues/280
    doc = {'letters': u'♄εℓł☺'}

    schema = {'letters': {'type': 'string', 'allowed': ['a', 'b', 'c']}}
    assert_fail(doc, schema)

    schema = {'letters': {'type': 'string', 'allowed': [u'♄εℓł☺']}}
    assert_success(doc, schema)

    schema = {'letters': {'type': 'string', 'allowed': ['♄εℓł☺']}}
    doc = {'letters': '♄εℓł☺'}
    assert_success(doc, schema)


def test_allowed_when_passing_list_of_dicts():
    # https://github.com/pyeve/cerberus/issues/524
    doc = {'letters': [{'some': 'dict'}]}
    schema = {'letters': {'type': 'list', 'allowed': ['a', 'b', 'c']}}

    assert_fail(
        doc,
        schema,
        error=(
            'letters',
            ('letters', 'allowed'),
            errors.UNALLOWED_VALUES,
            ['a', 'b', 'c'],
            (({'some': 'dict'},),),
        ),
    )
