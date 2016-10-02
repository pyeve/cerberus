# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import os
    import sys
    import unittest  # TODO pytest
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..', '..')))

from cerberus import (Validator, errors)  # noqa
from cerberus.tests import TestBase  # noqa


ValidationError = errors.ValidationError


class TestTestBase(TestBase):
    def _test_that_test_fails(self, test, *args):
        try:
            test(*args)
        except AssertionError as e:  # noqa
            pass
        else:
            raise AssertionError("test didn't fail")

    def test_fail(self):
        self._test_that_test_fails(self.assertFail, {'an_integer': 60})

    def test_success(self):
        self._test_that_test_fails(self.assertSuccess, {'an_integer': 110})


class TestAssorted(TestBase):
    def test_clear_cache(self):
        assert len(self.validator._valid_schemas) > 0
        self.validator.clear_caches()
        assert len(self.validator._valid_schemas) == 0

    def test_docstring(self):
        assert Validator.__doc__


if __name__ == '__main__':
    # TODO get pytest.main() working before tackling
    # https://github.com/nicolaiarocci/cerberus/issues/213
    unittest.main()
