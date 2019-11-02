from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_check_with_rule(validator):
    def check_with_name(field, value, error):
        if not value.islower():
            error(field, 'must be lowercase')

    validator.schema = {
        'name': {'check_with': check_with_name},
        'age': {'type': 'integer'},
    }

    assert_fail(
        {'name': 'ItsMe', 'age': 2},
        validator=validator,
        error=('name', (), errors.CUSTOM, None, ('must be lowercase',)),
    )
    assert validator.errors == {'name': ['must be lowercase']}
    assert_success({'name': 'itsme', 'age': 2}, validator=validator)
