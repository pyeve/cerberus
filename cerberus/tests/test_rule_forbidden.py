from pytest import mark

from cerberus.tests import assert_fail, assert_success


@mark.parametrize(
    ("test_function", "document"),
    [(assert_success, {'user': 'alice'}), (assert_fail, {'user': 'admin'})],
)
def test_forbidden(test_function, document):
    test_function(schema={'user': {'forbidden': ['root', 'admin']}}, document=document)


@mark.parametrize("document", [{'amount': 0}, {'amount': 0.0}])
def test_forbidden_number(document):
    assert_fail(schema={'amount': {'forbidden': (0, 0.0)}}, document=document)
