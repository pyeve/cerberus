import pytest

import cerberus
from cerberus.base import UnconcernedValidator
from cerberus.tests import assert_fail, assert_success
from cerberus.tests.conftest import sample_schema


def test_contextual_data_preservation():
    class InheritedValidator(cerberus.Validator):
        def __init__(self, *args, **kwargs):
            if 'working_dir' in kwargs:
                self.working_dir = kwargs['working_dir']
            super().__init__(*args, **kwargs)

        def _check_with_test(self, field, value):
            if self.working_dir:
                return True

    assert 'test' in InheritedValidator.checkers
    v = InheritedValidator(
        {'test': {'type': 'list', 'itemsrules': {'check_with': 'test'}}},
        working_dir='/tmp',
    )
    assert_success({'test': ['foo']}, validator=v)


def test_docstring_parsing():
    class CustomValidator(cerberus.Validator):
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


def test_check_with_method():
    # https://github.com/pyeve/cerberus/issues/265
    class MyValidator(cerberus.Validator):
        def _check_with_oddity(self, field, value):
            if not value & 1:
                self._error(field, "Must be an odd number")

    v = MyValidator(schema={'amount': {'check_with': 'oddity'}})
    assert_success(document={'amount': 1}, validator=v)
    assert_fail(
        document={'amount': 2},
        validator=v,
        error=('amount', (), cerberus.errors.CUSTOM, None, ('Must be an odd number',)),
    )


@pytest.mark.parametrize(
    'cls',
    (
        UnconcernedValidator,
        cerberus.validator_factory('NonvalidatingValidator', validated_schema=False),
    ),
)
def test_schema_validation_can_be_disabled(cls):
    v = cls(schema=sample_schema)
    assert v.validate(document={'an_integer': 1})
    assert not v.validate(document={'an_integer': 'a'})

    v.schema['an_integer']['tüpe'] = 'int'
    with pytest.raises(RuntimeError):
        v.validate(document={'an_integer': 1})
    v.schema['an_integer'].pop('tüpe')


def test_custom_datatype_rule():
    class MyValidator(cerberus.Validator):
        types_mapping = cerberus.Validator.types_mapping.copy()
        types_mapping['number'] = cerberus.TypeDefinition('number', (int,), ())

        def _validate_min_number(self, min_number, field, value):
            """ {'type': 'number'} """
            if value < min_number:
                self._error(field, 'Below the min')

    schema = {'test_field': {'min_number': 1, 'type': 'number'}}
    validator = MyValidator(schema)
    assert_fail(
        {'test_field': 0.0},
        validator=validator,
        error=('test_field', ('test_field', 'type'), cerberus.errors.TYPE, ('number',)),
    )
    assert_fail(
        {'test_field': 0},
        validator=validator,
        error=('test_field', (), cerberus.errors.CUSTOM, None, ('Below the min',)),
    )
    assert validator.errors == {'test_field': ['Below the min']}
