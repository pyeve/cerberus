from cerberus.tests import assert_fail, assert_success


def test_keysrules():
    schema = {
        'a_dict_with_keysrules': {
            'type': 'dict',
            'keysrules': {'type': 'string', 'regex': '[a-z]+'},
        }
    }
    assert_success({'a_dict_with_keysrules': {'key': 'value'}}, schema=schema)
    assert_fail({'a_dict_with_keysrules': {'KEY': 'value'}}, schema=schema)
