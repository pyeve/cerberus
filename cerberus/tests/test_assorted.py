# -*- coding: utf-8 -*-

from cerberus.tests import assert_fail, assert_success


def test_clear_cache(validator):
    assert len(validator._valid_schemas) > 0
    validator.clear_caches()
    assert len(validator._valid_schemas) == 0


def test_docstring(validator):
    assert validator.__doc__


# Test that tesing with the sample schema works as expected
# as there might be rules with side-effects in it

def _test_that_test_fails(test, *args):
    try:
        test(*args)
    except AssertionError:
        pass
    else:
        raise AssertionError("test didn't fail")


def test_fail():
    _test_that_test_fails(assert_fail, {'an_integer': 60})


def test_success():
    _test_that_test_fails(assert_success, {'an_integer': 110})
