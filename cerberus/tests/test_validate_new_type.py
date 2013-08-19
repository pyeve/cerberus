"""Tests for Validation of a new Type."""

import sys
import pytest

from cerberus import Validator


FILTER = {
    'limit': {
        'required': False,
        'type': 'number',
        'min_number': 1,
    },
}


class BaseValidator(Validator):
    """Validator for resources of the HTTP API."""

    def _validate_type_number(self, field, value):
        """Validates the string representing integer."""
        try:
            int(value)
        except ValueError:
            self._error("'{0}' is not a valid integer.".format(field))

    def _validate_min_number(self, min_value, field, value):
        """Validates the 'min_number' operation on the 'number' data type."""
        value = int(value)
        return super(BaseValidator, self)._validate_min(min_value, field, value)

    def _validate_max_number(self, max_value, field, value):
        """Validates the 'max_number' operation on the 'number' data type."""
        value = int(value)
        return super(BaseValidator, self)._validate_max(max_value, field, value)


class _Validator(BaseValidator):
    """Extention of Cerberus' validator, with custom types specific for events."""
    # Event specific validation hook


class ValidatorWrapper(object):
    """Wraps the validator, automating schema selection
    and raising validation errors.
    """

    def validate_or_raise(self, document, schema=None):
        """Call validate and raise a ValidationError if it returns False."""
        if not self.validate(document, schema):
            raise MyException(
                description=u'\n'.join(self.validator.errors),
            )

    def validate(self, document, schema=None):
        """Override the `validate` method."""
        if schema is None:
            schema = self.validator.schema

        if document is None:
            document = {}

        return self.validator.validate(document, schema)


class FilterValidator(ValidatorWrapper):
    """Validator for the schema FILTER."""

    def __init__(self, *args, **kwargs):
        self.validator = _Validator(schema=FILTER)
        super(FilterValidator, self).__init__(*args, **kwargs)


class MyException(Exception):
    """Generic error."""

    def __init__(self, description=None, exc=None, **kwargs):
        if exc:
            trace = sys.exc_info()[2]
            raise MyException(description=description, **kwargs), None, trace
        self.description = description
        self.kwargs = kwargs
        super(MyException, self).__init__(unicode(self))

    def __unicode__(self):
        result = []
        result.append(self.description or 'MyException')
        if self.kwargs:
            args = ['='.join(str(x) for x in self.kwargs.iteritems())]
            result.append(','.join(args))
        return format_message(u' '.join(result))


def format_message(msg):
    """Capitalize a message and add a stop at the end if necessary."""
    if not msg.endswith('.'):
        msg += '.'
    return msg.capitalize()


def test_type_number():
    document = {'limit': '5'}
    assert FilterValidator().validate_or_raise(document) is None

    document = {'limit': 5}
    assert FilterValidator().validate_or_raise(document) is None

    document = {'limit': ''}
    with pytest.raises(ValueError):
        FilterValidator().validate_or_raise(document)

