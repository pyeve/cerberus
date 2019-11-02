from cerberus import Validator
from cerberus.tests import assert_normalized


def test_rename():
    assert_normalized(
        schema={'foo': {'rename': 'bar'}, 'bar': {}},
        document={'foo': 0},
        expected={'bar': 0},
    )


def test_rename_handler_in_allow_unknown():
    assert_normalized(
        schema={},
        document={'0': 'foo'},
        expected={0: 'foo'},
        validator=Validator(allow_unknown={'rename_handler': int}),
    )
