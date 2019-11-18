from copy import deepcopy
from tempfile import NamedTemporaryFile

from cerberus import Validator
from cerberus.tests import assert_normalized, assert_success


def test_normalized():
    schema = {'amount': {'coerce': int}}
    document = {'amount': '2'}
    expected = {'amount': 2}
    assert_normalized(document, expected, schema)


def test_normalize_complex_objects():
    # https://github.com/pyeve/cerberus/issues/147
    schema = {'revision': {'coerce': int}}
    document = {'revision': '5', 'file': NamedTemporaryFile(mode='w+')}
    document['file'].write(r'foobar')
    document['file'].seek(0)
    normalized = Validator(schema, allow_unknown=True).normalized(document)
    assert normalized['revision'] == 5
    assert normalized['file'].read() == 'foobar'
    document['file'].close()
    normalized['file'].close()


def test_normalize_does_not_change_input_document():
    # https://github.com/pyeve/cerberus/issues/147
    schema = {'thing': {'type': 'dict', 'schema': {'amount': {'coerce': int}}}}
    ref_obj = '2'
    document = {'thing': {'amount': ref_obj}}
    normalized = Validator(schema).normalized(document)
    assert document is not normalized
    assert normalized['thing']['amount'] == 2
    assert document['thing']['amount'] is ref_obj


def test_normalize_tuples():
    # https://github.com/pyeve/cerberus/issues/271
    schema = {
        'my_field': {
            'type': 'tuple',
            'itemsrules': {'type': ('string', 'number', 'dict')},
        }
    }
    document = {'my_field': ('foo', 'bar', 42, 'albert', 'kandinsky', {'items': 23})}
    assert_success(document, schema)

    normalized = Validator(schema).normalized(document)
    assert normalized['my_field'] == (
        'foo',
        'bar',
        42,
        'albert',
        'kandinsky',
        {'items': 23},
    )


def test_purge_readonly():
    schema = {
        'description': {'type': 'string', 'maxlength': 500},
        'last_updated': {'readonly': True},
    }
    validator = Validator(schema=schema, purge_readonly=True)
    document = {'description': 'it is a thing'}
    expected = deepcopy(document)
    document['last_updated'] = 'future'
    assert_normalized(document, expected, validator=validator)


def test_purge_unknown():
    validator = Validator(purge_unknown=True)
    schema = {'foo': {'type': 'string'}}
    document = {'bar': 'foo'}
    expected = {}
    assert_normalized(document, expected, schema, validator)


def test_purge_unknown_in_subschema():
    schema = {
        'foo': {
            'type': 'dict',
            'schema': {'foo': {'type': 'string'}},
            'purge_unknown': True,
        }
    }
    document = {'foo': {'bar': ''}}
    expected = {'foo': {}}
    assert_normalized(document, expected, schema)


def test_oneof_normalization():
    # inserting a default
    schema = {
        'foo': {'type': 'string'},
        'bar': {
            'oneof': [
                {'dependencies': {"foo": "B"}, 'default': "B"},
                {'dependencies': {"foo": "A"}, 'default': "C"},
            ]
        },
    }
    document = {'foo': 'A'}
    expected = {'foo': 'A', 'bar': "C"}
    assert_normalized(document, expected, schema)

    # overwriting None if not nullable
    document = {'foo': 'A', 'bar': None}
    assert_normalized(document, expected, schema)

    # using a sub-schema inside oneof
    subschema = {
        "field1": {"type": "number"},
        "field2": {"type": "number", 'default': 2},
    }
    schema = {
        'foo': {'type': 'string'},
        'bar': {
            'type': 'dict',
            'oneof': [
                {'dependencies': {"^foo": "B"}, 'schema': subschema},
                {'dependencies': {"^foo": "A"}, 'default': "C"},
            ],
        },
    }
    document = {'foo': 'B', 'bar': {"field1": 1}}
    expected = {'foo': 'B', 'bar': {"field1": 1, "field2": 2}}
    assert_normalized(document, expected, schema)

    # do not normalize if oneof is not fullfilled
    schema = {
        'foo': {'type': 'string'},
        'bar': {
            'oneof': [
                {'dependencies': {"foo": "A"}, 'default': "B"},
                {'dependencies': {"foo": "A"}, 'default': "C"},
            ]
        },
    }
    expected = {'foo': 'A', 'bar': None}
    document = {'foo': 'A', 'bar': None}

    validator = Validator(schema)
    assert validator.normalized(document) == expected
