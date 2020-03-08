from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_not_has_error, assert_success


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': 5}),
        (assert_fail, {'field': -1}),
        (assert_fail, {'field': 11}),
    ],
)
def test_allof(test_function, document):
    test_function(
        schema={'field': {'allof': [{'type': 'integer'}, {'min': 0}, {'max': 10}]}},
        document=document,
    )


def test_anyof_fails():
    schema = {'field': {'type': 'integer', 'anyof': [{'min': 0}, {'min': 10}]}}
    assert_fail(
        document={'field': -1},
        schema=schema,
        error=(('field',), ('field', 'anyof'), errors.ANYOF, ({'min': 0}, {'min': 10})),
        child_errors=[
            (('field',), ('field', 'anyof', 0, 'min'), errors.MIN_VALUE, 0),
            (('field',), ('field', 'anyof', 1, 'min'), errors.MIN_VALUE, 10),
        ],
    )

    assert_fail(document={'field': 5.5}, schema=schema)
    assert_fail(document={'field': '5.5'}, schema=schema)

    assert_fail(
        schema={'field': {'anyof': [{'min': 0, 'max': 10}, {'min': 100, 'max': 110}]}},
        document={'field': 50},
    )


@mark.parametrize(
    ("schema", "document"),
    [
        ({'field': {'min': 0, 'max': 10}}, {'field': 5}),
        (
            {'field': {'anyof': [{'min': 0, 'max': 10}, {'min': 100, 'max': 110}]}},
            {'field': 105},
        ),
        (
            {'field': {'type': 'integer', 'anyof': [{'min': 0}, {'min': 10}]}},
            {'field': 10},
        ),
        (
            {'field': {'type': 'integer', 'anyof': [{'min': 0}, {'min': 10}]}},
            {'field': 5},
        ),
    ],
)
def test_anyof_succeeds(schema, document):
    assert_success(schema=schema, document=document)


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': -1.5}),
        (assert_success, {'field': -1}),
        (assert_success, {'field': 11}),
        (assert_success, {'field': 11.5}),
        (assert_fail, {'field': 5}),
        (assert_fail, {'field': 5.5}),
        (assert_fail, {'field': '5.5'}),
    ],
)
def test_anyof_in_allof(test_function, document):
    test_function(
        schema={
            'field': {
                'allof': [
                    {'anyof': [{'type': 'float'}, {'type': 'integer'}]},
                    {'anyof': [{'min': 10}, {'max': 0}]},
                ]
            }
        },
        document=document,
    )


def test_anyof_in_itemsrules(validator):
    # test that a list of schemas can be specified.

    valid_parts = (
        {
            'schema': {
                'model number': {'type': ('string',)},
                'count': {'type': ('integer',)},
            }
        },
        {'schema': {'serial number': {'type': (str,)}, 'count': {'type': (int,)}}},
    )
    valid_item = {'type': ('dict', 'string'), 'anyof': valid_parts}
    schema = {'parts': {'type': 'list', 'itemsrules': valid_item}}
    document = {
        'parts': [
            {'model number': 'MX-009', 'count': 100},
            {'serial number': '898-001'},
            'misc',
        ]
    }

    # document is valid. each entry in 'parts' matches a type or schema
    assert_success(document=document, schema=schema, validator=validator)

    document['parts'].append({'product name': "Monitors", 'count': 18})
    # document is invalid. 'product name' does not match any valid schemas
    assert_fail(document=document, schema=schema, validator=validator)

    document['parts'].pop()
    # document is valid again
    assert_success(document=document, schema=schema, validator=validator)

    document['parts'].append({'product name': "Monitors", 'count': 18})
    document['parts'].append(10)
    # and invalid. numbers are not allowed.
    _errors = assert_fail(
        document,
        schema,
        validator=validator,
        error=('parts', ('parts', 'itemsrules'), errors.ITEMSRULES, valid_item),
        child_errors=[
            (('parts', 3), ('parts', 'itemsrules', 'anyof'), errors.ANYOF, valid_parts),
            (
                ('parts', 4),
                ('parts', 'itemsrules', 'type'),
                errors.TYPE,
                ('dict', 'string'),
            ),
        ],
    )
    assert_not_has_error(
        _errors,
        ('parts', 4),
        ('parts', 'itemsrules', 'anyof'),
        errors.ANYOF,
        valid_parts,
    )

    # tests errors.BasicErrorHandler's tree representation
    _errors = validator.errors
    assert 'parts' in _errors
    assert 3 in _errors['parts'][-1]
    assert _errors['parts'][-1][3][0] == "no definitions validate"
    scope = _errors['parts'][-1][3][-1]
    assert 'anyof definition 0' in scope
    assert 'anyof definition 1' in scope
    assert scope['anyof definition 0'] == [{"product name": ["unknown field"]}]
    assert scope['anyof definition 1'] == [{"product name": ["unknown field"]}]
    assert _errors['parts'][-1][4] == ["must be one of these types: ('dict', 'string')"]


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': {'val': 0}}),
        (assert_success, {'field': {'val': '0'}}),
        (assert_fail, {'field': {'val': 1.1}}),
    ],
)
def test_anyof_with_semantically_equal_schemas(test_function, document):
    test_function(
        schema={
            'field': {
                'anyof': [
                    {'type': 'dict', 'schema': {'val': {'type': 'integer'}}},
                    {'type': 'dict', 'schema': {'val': {'type': 'string'}}},
                ]
            }
        },
        document=document,
    )
    test_function(
        schema={
            'field': {
                'type': 'dict',
                'anyof': [
                    {'schema': {'val': {'type': 'integer'}}},
                    {'schema': {'val': {'type': 'string'}}},
                ],
            }
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': -1}),
        (assert_fail, {'field': -5}),
        (assert_fail, {'field': 1}),
        (assert_fail, {'field': 5}),
        (assert_fail, {'field': 11}),
        (assert_fail, {'field': 15}),
    ],
)
def test_noneof(test_function, document):
    test_function(
        schema={
            'field': {
                'type': 'integer',
                'noneof': [{'min': 0}, {'min': 10}, {'allowed': [-5, 5, 15]}],
            }
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'field': -5}),
        (assert_success, {'field': 1}),
        (assert_fail, {'field': -1}),
        (assert_fail, {'field': 5}),
        (assert_fail, {'field': 11}),
        (assert_fail, {'field': 15}),
    ],
)
def test_oneof(test_function, document):
    test_function(
        schema={
            'field': {
                'type': 'integer',
                'oneof': [{'min': 0}, {'min': 10}, {'allowed': [-5, 5, 15]}],
            }
        },
        document=document,
    )


def test_schema_is_not_spoiled(validator):
    validator.schema = {
        'field': {'type': 'integer', 'anyof': [{'min': 0}, {'min': 10}]}
    }
    assert 'type' not in validator.schema['field']['anyof'][0]
    assert 'type' not in validator.schema['field']['anyof'][1]
    assert 'allow_unknown' not in validator.schema['field']['anyof'][0]
    assert 'allow_unknown' not in validator.schema['field']['anyof'][1]


@mark.parametrize("document", [{'field': 'bar'}, {'field': 23}])
def test_anyof_type(document):
    assert_success(
        schema={'field': {'anyof_type': ['string', 'integer']}}, document=document
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'oneof_schema': {'digits': 19}}),
        (assert_success, {'oneof_schema': {'text': '84'}}),
        (assert_fail, {'oneof_schema': {'digits': 19, 'text': '84'}}),
    ],
)
def test_oneof_schema(test_function, document):
    test_function(
        schema={
            'oneof_schema': {
                'type': 'dict',
                'oneof_schema': [
                    {'digits': {'type': 'integer', 'min': 0, 'max': 99}},
                    {'text': {'type': 'string', 'regex': '^[0-9]{2}$'}},
                ],
            }
        },
        document=document,
    )


@mark.parametrize(
    "document", [{'nested_oneof_type': {'foo': 'a'}}, {'nested_oneof_type': {'bar': 3}}]
)
def test_oneof_type_in_valuesrules(document):
    assert_success(
        schema={
            'nested_oneof_type': {'valuesrules': {'oneof_type': ['string', 'integer']}}
        },
        document=document,
    )


def test_oneof_type_in_oneof_schema(validator):
    assert_fail(
        schema={
            'abc': {
                'type': 'dict',
                'oneof_schema': [
                    {
                        'foo': {
                            'type': 'dict',
                            'schema': {'bar': {'oneof_type': ['integer', 'float']}},
                        }
                    },
                    {'baz': {'type': 'string'}},
                ],
            }
        },
        document={'abc': {'foo': {'bar': 'bad'}}},
        validator=validator,
    )

    assert validator.errors == {
        'abc': [
            'none or more than one rule validate',
            {
                'oneof definition 0': [
                    {
                        'foo': [
                            {
                                'bar': [
                                    'none or more than one rule validate',
                                    {
                                        'oneof definition 0': [
                                            "must be one of these types: ('integer',)"
                                        ],
                                        'oneof definition 1': [
                                            "must be one of these " "types: ('float',)"
                                        ],
                                    },
                                ]
                            }
                        ]
                    }
                ],
                'oneof definition 1': [{'foo': ['unknown field']}],
            },
        ]
    }


def test_allow_unknown_in_oneof():
    # https://github.com/pyeve/cerberus/issues/251
    schema = {
        'test': {
            'oneof': (
                {
                    'type': ('dict',),
                    'allow_unknown': True,
                    'schema': {'known': {'type': ('string',)}},
                },
                {'type': ('dict',), 'schema': {'known': {'type': ('string',)}}},
            )
        }
    }

    # check regression and that allow unknown does not cause any different
    # than expected behaviour for one-of.
    assert_fail(
        schema=schema,
        document={'test': {'known': 's'}},
        error=('test', ('test', 'oneof'), errors.ONEOF, schema['test']['oneof']),
    )

    # check that allow_unknown is actually applied
    assert_success(document={'test': {'known': 's', 'unknown': 'asd'}}, schema=schema)
