from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_regex(validator):
    field = 'a_regex_email'

    assert_success({field: 'valid.email@gmail.com'}, validator=validator)

    assert_fail(
        {field: 'invalid'},
        update=True,
        error=(
            field,
            (field, 'regex'),
            errors.REGEX_MISMATCH,
            r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
        ),
    )


def test_regex_with_flag():
    assert_success({"item": "hOly grAil"}, {"item": {"regex": "(?i)holy grail"}})
    assert_fail({"item": "hOly grAil"}, {"item": {"regex": "holy grail"}})
