from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'this_field': {}}),
        (assert_success, {'that_field': {}}),
        (assert_success, {}),
        (assert_fail, {'that_field': {}, 'this_field': {}}),
    ],
)
def test_excludes(test_function, document):
    test_function(
        schema={
            'this_field': {'type': 'dict', 'excludes': 'that_field'},
            'that_field': {'type': 'dict'},
        },
        document=document,
    )


def test_excludes_basic_error_handler_message(validator):
    assert_fail(
        document={'that_field': {}, 'this_field': {}},
        schema={
            'this_field': {
                'type': 'dict',
                'excludes': ['that_field', 'bazo_field'],
                'required': True,
            },
            'that_field': {'type': 'dict', 'excludes': 'this_field', 'required': True},
        },
        validator=validator,
    )
    message = errors.BasicErrorHandler.messages[errors.EXCLUDES_FIELD.code]
    assert validator.errors == {
        'that_field': [message.format("'this_field'", field="that_field")],
        'this_field': [
            message.format("'that_field', 'bazo_field'", field="this_field")
        ],
    }


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'this_field': {}}),
        (assert_success, {'that_field': {}}),
        (assert_success, {'that_field': {}, 'bazo_field': {}}),
        (assert_fail, {'this_field': {}, 'that_field': {}}),
        (assert_fail, {'this_field': {}, 'bazo_field': {}}),
        (assert_fail, {'that_field': {}, 'this_field': {}, 'bazo_field': {}}),
    ],
)
def test_excludes_of_multiple_fields(test_function, document):
    test_function(
        schema={
            'this_field': {'type': 'dict', 'excludes': ['that_field', 'bazo_field']},
            'that_field': {'type': 'dict', 'excludes': 'this_field'},
            'bazo_field': {'type': 'dict'},
        },
        document=document,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'this_field': {}}),
        (assert_success, {'that_field': {}}),
        (assert_fail, {}),
        (assert_fail, {'that_field': {}, 'this_field': {}}),
    ],
)
def test_excludes_of_required_fields(test_function, document):
    test_function(
        schema={
            'this_field': {'type': 'dict', 'excludes': 'that_field', 'required': True},
            'that_field': {'type': 'dict', 'excludes': 'this_field', 'required': True},
        },
        document=document,
        update=False,
    )


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'this_field': {}}),
        (assert_success, {'that_field': {}}),
        (assert_success, {}),
        (assert_fail, {'that_field': {}, 'this_field': {}}),
    ],
)
def test_mutual_excludes(test_function, document):
    test_function(
        schema={
            'this_field': {'type': 'dict', 'excludes': 'that_field'},
            'that_field': {'type': 'dict', 'excludes': 'this_field'},
        },
        document=document,
    )
