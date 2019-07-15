from cerberus import errors
from cerberus.tests import assert_fail


def test_items(validator):
    field = 'a_list_of_values'
    value = ['a string', 'not an integer']
    assert_fail(
        document={field: value},
        validator=validator,
        error=(
            field,
            (field, 'items'),
            errors.ITEMS,
            ({'type': ('string',)}, {'type': ('integer',)}),
        ),
        child_errors=[
            ((field, 1), (field, 'items', 1, 'type'), errors.TYPE, ('integer',))
        ],
    )

    assert (
        errors.BasicErrorHandler.messages[errors.TYPE.code].format(
            constraint=('integer',)
        )
        in validator.errors[field][-1][1]
    )


def test_items_with_extra_item():
    field = 'a_list_of_values'
    assert_fail(
        document={field: ['a string', 10, 'an extra item']},
        error=(
            field,
            (field, 'items'),
            errors.ITEMS_LENGTH,
            ({'type': ('string',)}, {'type': ('integer',)}),
            (2, 3),
        ),
    )
