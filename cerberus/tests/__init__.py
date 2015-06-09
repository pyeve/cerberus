import unittest
from ..cerberus import Validator, SchemaError, ValidationError, errors


class TestBase(unittest.TestCase):

    required_string_extension = {
        'a_required_string': {'type': 'string',
                              'minlength': 2,
                              'maxlength': 10,
                              'required': True}}

    def setUp(self):
        self.document = {'name': 'john doe'}
        self.schema = {
            'a_string': {'type': 'string',
                         'minlength': 2,
                         'maxlength': 10},
            'a_nullable_integer': {
                'type': 'integer',
                'nullable': True
            },
            'an_integer': {
                'type': 'integer',
                'min': 1,
                'max': 100,
            },
            'a_restricted_integer': {
                'type': 'integer',
                'allowed': [-1, 0, 1],
            },
            'a_boolean': {
                'type': 'boolean',
            },
            'a_datetime': {
                'type': 'datetime',
            },
            'a_float': {
                'type': 'float',
                'min': 1,
                'max': 100,
            },
            'a_number': {
                'type': 'number',
                'min': 1,
                'max': 100,
            },
            'a_set': {
                'type': 'set',
            },
            'one_or_more_strings': {
                'type': ['string', 'list'],
                'schema': {'type': 'string'}
            },
            'a_regex_email': {
                'type': 'string',
                'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            },
            'a_readonly_string': {
                'type': 'string',
                'readonly': True,
            },
            'a_restricted_string': {
                'type': 'string',
                'allowed': ["agent", "client", "vendor"],
            },
            'an_array': {
                'type': 'list',
                'allowed': ["agent", "client", "vendor"],
            },
            'a_list_of_dicts_deprecated': {
                'type': 'list',
                'items': {
                    'sku': {'type': 'string'},
                    'price': {'type': 'integer'},
                },
            },
            'a_list_of_dicts': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'sku': {'type': 'string'},
                        'price': {'type': 'integer'},
                    },
                },
            },
            'a_list_of_values': {
                'type': 'list',
                'items': [{'type': 'string'}, {'type': 'integer'}, ]
            },
            'a_list_of_integers': {
                'type': 'list',
                'schema': {'type': 'integer'},
            },
            'a_dict': {
                'type': 'dict',
                'schema': {
                    'address': {'type': 'string'},
                    'city': {'type': 'string', 'required': True}
                },
            },
            'a_dict_with_valueschema': {
                'type': 'dict',
                'valueschema': {'type': 'integer'}
            },
            'a_dict_with_propertyschema': {
                'type': 'dict',
                'propertyschema': {'type': 'string', 'regex': '[a-z]+'}
            },
            'a_list_length': {
                'type': 'list',
                'schema': {'type': 'integer'},
                'minlength': 2,
                'maxlength': 5,
            },
            'a_nullable_field_without_type': {
                'nullable': True
            },
            'a_not_nullable_field_without_type': {
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
        except Exception as e:  # noqa
            self.fail("%s not raised." % known_exception)

    def assertFail(self, document, schema=None, validator=None):
        if validator is None:
            validator = self.validator
        self.assertFalse(validator.validate(document, schema))

    def assertSuccess(self, document, schema=None, validator=None):
        if validator is None:
            validator = self.validator
        self.assertTrue(validator.validate(document, schema, update=True),
                        validator.errors)

    def assertError(self, field, error, validator=None):
        if validator is None:
            validator = self.validator
        self.assertTrue(error in validator.errors.get(field, {}))

    def assertNoError(self, field, error, validator=None):
        if validator is None:
            validator = self.validator
        errs = validator.errors.get(field, {})
        self.assertFalse(error in errs)

    def assertBadType(self, field, data_type, value):
        doc = {field: value}
        self.assertFail(doc)
        self.assertError(field, errors.ERROR_BAD_TYPE.format(data_type))
