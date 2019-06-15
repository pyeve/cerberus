from cerberus import Validator, errors
from cerberus.tests import assert_fail, assert_has_error, assert_normalized


def test_coerce():
    assert_normalized(
        schema={'amount': {'coerce': int}},
        document={'amount': '1'},
        expected={'amount': 1},
    )


def test_coerce_chain():
    drop_prefix = lambda x: x[2:]  # noqa: E731
    upper = lambda x: x.upper()  # noqa: E731
    assert_normalized(
        schema={'foo': {'coerce': [hex, drop_prefix, upper]}},
        document={'foo': 15},
        expected={'foo': 'F'},
    )


def test_coerce_chain_aborts(validator):
    def dont_do_me(value):
        raise AssertionError('The coercion chain did not abort after an error.')

    validator({'foo': '0'}, schema={'foo': {'coerce': [hex, dont_do_me]}})
    assert errors.COERCION_FAILED in validator._errors


def test_coerce_does_not_input_data():
    validator = Validator({'amount': {'coerce': int}})
    document = {'amount': '1'}
    validator.validate(document)
    assert validator.document is not document


def test_coerce_in_allow_unknown():
    assert_normalized(
        schema={'foo': {'schema': {}, 'allow_unknown': {'coerce': int}}},
        document={'foo': {'bar': '0'}},
        expected={'foo': {'bar': 0}},
    )


def test_coerce_in_items():
    schema = {'things': {'type': 'list', 'items': [{'coerce': int}, {'coerce': str}]}}
    document = {'things': ['1', 2]}
    expected = {'things': [1, '2']}
    assert_normalized(document, expected, schema)

    validator = Validator(schema)
    document['things'].append(3)
    assert not validator(document)
    assert validator.document['things'] == document['things']


def test_coercion_of_sequence_items_with_float_values(validator):
    # https://github.com/pyeve/cerberus/issues/161
    assert_normalized(
        schema={
            'a_list': {'type': 'list', 'itemsrules': {'type': 'float', 'coerce': float}}
        },
        document={'a_list': [3, 4, 5]},
        expected={'a_list': [3.0, 4.0, 5.0]},
        validator=validator,
    )


def test_coerce_in_itemsrules_with_integer_values():
    assert_normalized(
        schema={'things': {'type': 'list', 'itemsrules': {'coerce': int}}},
        document={'things': ['1', '2', '3']},
        expected={'things': [1, 2, 3]},
    )


def test_coerce_in_itemsrules_fails(validator):
    # https://github.com/pyeve/cerberus/issues/211
    schema = {
        'data': {'type': 'list', 'itemsrules': {'type': 'integer', 'coerce': int}}
    }
    document = {'data': ['q']}
    assert validator.validated(document, schema) is None
    assert (
        validator.validated(document, schema, always_return_document=True) == document
    )  # noqa: W503


def test_coerce_in_keysrules():
    # https://github.com/pyeve/cerberus/issues/155
    assert_normalized(
        schema={
            'thing': {'type': 'dict', 'keysrules': {'coerce': int, 'type': 'integer'}}
        },
        document={'thing': {'5': 'foo'}},
        expected={'thing': {5: 'foo'}},
    )


def test_coerce_in_schema():
    assert_normalized(
        schema={'thing': {'type': 'dict', 'schema': {'amount': {'coerce': int}}}},
        document={'thing': {'amount': '2'}},
        expected={'thing': {'amount': 2}},
    )


def test_coerce_in_schema_in_itemsrules():
    assert_normalized(
        schema={
            'things': {
                'type': 'list',
                'itemsrules': {'type': 'dict', 'schema': {'amount': {'coerce': int}}},
            }
        },
        document={'things': [{'amount': '2'}]},
        expected={'things': [{'amount': 2}]},
    )


def test_coerce_in_valuesrules():
    # https://github.com/pyeve/cerberus/issues/155
    assert_normalized(
        schema={
            'thing': {'type': 'dict', 'valuesrules': {'coerce': int, 'type': 'integer'}}
        },
        document={'thing': {'amount': '2'}},
        expected={'thing': {'amount': 2}},
    )


def test_coerce_catches_ValueError():
    schema = {'amount': {'coerce': int}}
    _errors = assert_fail({'amount': 'not_a_number'}, schema)
    _errors[0].info = ()  # ignore exception message here
    assert_has_error(
        _errors, 'amount', ('amount', 'coerce'), errors.COERCION_FAILED, int
    )


def test_coerce_in_listitems_catches_ValueError():
    schema = {'things': {'type': 'list', 'items': [{'coerce': int}, {'coerce': str}]}}
    document = {'things': ['not_a_number', 2]}
    _errors = assert_fail(document, schema)
    _errors[0].info = ()  # ignore exception message here
    assert_has_error(
        _errors,
        ('things', 0),
        ('things', 'items', 'coerce'),
        errors.COERCION_FAILED,
        int,
    )


def test_coerce_catches_TypeError():
    schema = {'name': {'coerce': str.lower}}
    _errors = assert_fail({'name': 1234}, schema)
    _errors[0].info = ()  # ignore exception message here
    assert_has_error(
        _errors, 'name', ('name', 'coerce'), errors.COERCION_FAILED, str.lower
    )


def test_coerce_in_listitems_catches_TypeError():
    schema = {
        'things': {'type': 'list', 'items': [{'coerce': int}, {'coerce': str.lower}]}
    }
    document = {'things': ['1', 2]}
    _errors = assert_fail(document, schema)
    _errors[0].info = ()  # ignore exception message here
    assert_has_error(
        _errors,
        ('things', 1),
        ('things', 'items', 'coerce'),
        errors.COERCION_FAILED,
        str.lower,
    )


def test_custom_coerce_and_rename():
    class MyNormalizer(Validator):
        def __init__(self, multiplier, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.multiplier = multiplier

        def _normalize_coerce_multiply(self, value):
            return value * self.multiplier

    v = MyNormalizer(2, {'foo': {'coerce': 'multiply'}})
    assert v.normalized({'foo': 2})['foo'] == 4

    v = MyNormalizer(3, allow_unknown={'rename_handler': 'multiply'})
    assert v.normalized({3: None}) == {9: None}
