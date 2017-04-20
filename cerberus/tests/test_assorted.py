# -*- coding: utf-8 -*-

from pytest import mark

from cerberus.tests import assert_fail, assert_success


def test_clear_cache(validator):
    assert len(validator._valid_schemas) > 0
    validator.clear_caches()
    assert len(validator._valid_schemas) == 0


def test_docstring(validator):
    assert validator.__doc__


# Test that testing with the sample schema works as expected
# as there might be rules with side-effects in it

@mark.parametrize('test,document', ((assert_fail, {'an_integer': 60}),
                                    (assert_success, {'an_integer': 110})))
def test_that_test_fails(test, document):
    try:
        test(document)
    except AssertionError:
        pass
    else:
        raise AssertionError("test didn't fail")
