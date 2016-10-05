# -*- coding: utf-8 -*-

from cerberus import Validator
from cerberus.tests import assert_success


def test_contextual_data_preservation():

    class InheritedValidator(Validator):
        def __init__(self, *args, **kwargs):
            if 'working_dir' in kwargs:
                self.working_dir = kwargs['working_dir']
            super(InheritedValidator, self).__init__(*args, **kwargs)

        def _validate_type_test(self, value):
            if self.working_dir:
                return True

    assert 'test' in InheritedValidator.types
    v = InheritedValidator({'test': {'type': 'list',
                                     'schema': {'type': 'test'}}},
                           working_dir='/tmp')
    assert_success({'test': ['foo']}, validator=v)


def test_docstring_parsing():
    class CustomValidator(Validator):
        def _validate_foo(self, argument, field, value):
            """ {'type': 'zap'} """
            pass

        def _validate_bar(self, value):
            """ Test the barreness of a value.

            The rule's arguments are validated against this schema:
                {'type': 'boolean'}
            """
            pass

    assert 'foo' in CustomValidator.validation_rules
    assert 'bar' in CustomValidator.validation_rules
