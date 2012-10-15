import unittest
from ..cerberus import *


class TestBase(unittest.TestCase):

    def setUp(self):
        self.document = {'name': 'john doe'}
        self.schema = {
            'a_required_string': {
                'type': 'string',
                'minlength': 2,
                'maxlength': 10,
                'required': True,
            },
            'an_integer': {
                'type': 'integer',
                'min': 1,
                'max': 100,
            },
            'a_boolean': {
                'type': 'boolean',
            },
            'a_datetime': {
                'type': 'datetime',
            },
            'a_readonly_string': {
                'type': 'string',
                'readonly': True,
            },
            'an_array': {
                'type': 'list',
                'allowed': ["agent", "client", "vendor"],
            },
            'a_list_of_dicts': {
                'type': 'list',
                'items': {
                    'sku': {'type': 'string'},
                    'price': {'type': 'integer'},
                },
            },
            'a_list_of_values': {
                'type': 'list',
                'items': [{'type': 'string'}, {'type': 'integer'}, ]
            },
            'a_dict': {
                'type': 'dict',
                'schema': {
                    'address': {'type': 'string'},
                    'city': {'type': 'string', 'required': True}
                },
            },
        }
        self.validator = Validator(self.schema)

    def assertSchemaError(self, document, schema=None, validator=None,
                          msg=None):
        self.assertException(SchemaError, document, schema, validator, msg)

    def assertValidationError(self, document, schema=None, validator=None,
                              msg=None):
        self.assertException(ValidationError, document, schema, validator, msg)

    def assertException(self, known_exception, document, schema=None,
                        validator=None, msg=None):
        if validator is None:
            validator = self.validator
        try:
            validator.validate(document, schema)
        except known_exception as e:
            self.assertTrue(msg == str(e)) if msg else self.assertTrue(True)
        except Exception as e:
            self.fail("%s not raised." % known_exception)

    def assertFail(self, document, schema=None, validator=None):
        if validator is None:
            validator = self.validator
        self.assertFalse(validator.validate(document, schema))

    def assertSuccess(self, document, schema=None, validator=None):
        if validator is None:
            validator = self.validator
        self.assertTrue(validator.validate_update(document, schema))

    def assertError(self, error, validator=None):
        if validator is None:
            validator = self.validator
        self.assertTrue(error in validator.errors)

    def assertBadType(self, field, data_type, value):
        doc = {field: value}
        self.assertFail(doc)
        self.assertError(ERROR_BAD_TYPE % (field, data_type))
