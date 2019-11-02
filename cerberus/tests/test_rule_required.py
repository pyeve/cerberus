from cerberus import errors
from cerberus.tests import assert_fail


def test_required():
    field = 'a_required_string'
    assert_fail(
        schema={'an_integer': {'type': 'integer'}, field: {'required': True}},
        document={'an_integer': 1},
        error=(field, (field, 'required'), errors.REQUIRED_FIELD, True),
    )
