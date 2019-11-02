from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


@mark.parametrize('constraint', (('Graham Chapman', 'Eric Idle'), 'Terry Gilliam'))
def test_contains_succeeds(constraint):
    assert_success(
        schema={'actors': {'contains': constraint}},
        document={'actors': ('Graham Chapman', 'Eric Idle', 'Terry Gilliam')},
    )


@mark.parametrize('constraint', (('Graham Chapman', 'Eric Idle'), 'Terry Gilliam'))
def test_contains_fails(validator, constraint):
    assert_fail(
        document={
            'actors': ('Eric idle', 'Terry Jones', 'John Cleese', 'Michael ' 'Palin')
        },
        schema={'actors': {'contains': constraint}},
        validator=validator,
    )

    assert errors.MISSING_MEMBERS in validator.document_error_tree['actors']

    missing_actors = validator.document_error_tree['actors'][
        errors.MISSING_MEMBERS
    ].info[0]
    assert any(x in missing_actors for x in ('Eric Idle', 'Terry Gilliam'))
