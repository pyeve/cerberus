from ..cerberus import *
from datetime import datetime
from random import choice
from string import lowercase
from cerberus.tests import TestBase


class TestValidator(TestBase):

    def test_empty_schema(self):
        v = Validator()
        self.assertSchemaError(self.document, None, v, ERROR_SCHEMA_MISSING)

    def test_bad_schema_type(self):
        schema = "this string should really be  dict"
        v = Validator(schema)
        self.assertSchemaError(self.document, None, v,
                               ERROR_SCHEMA_FORMAT % schema)

        v = Validator()
        self.assertSchemaError(self.document, schema, v,
                               ERROR_SCHEMA_FORMAT % schema)

    def test_empty_document(self):
        self.assertValidationError(None, None, None, ERROR_DOCUMENT_MISSING)

    def test_bad_document_type(self):
        document = "not a dict"
        self.assertValidationError(document, None, None,
                                   ERROR_DOCUMENT_FORMAT % document)

    def test_bad_schema_definition(self):
        field = 'name'
        schema = {field: 'this should really be a dict'}
        self.assertSchemaError(self.document, schema, None,
                               ERROR_DEFINITION_FORMAT % field)

    def test_unknown_field(self):
        field = 'surname'
        self.assertFail({field: 'doe'})
        self.assertError(ERROR_UNKNOWN_FIELD % field)

    def test_unknown_rule(self):
        field = 'name'
        schema = {field: {'unknown_rule': True, 'type': 'string'}}
        self.assertSchemaError(self.document, schema, None,
                               ERROR_UNKNOWN_RULE % ('unknown_rule', field))

    def test_required_field(self):
        self.assertFail({'an_integer': 1})
        self.assertError(ERROR_REQUIRED_FIELD % 'a_required_string')

    def test_readonly_field(self):
        field = 'a_readonly_string'
        self.assertFail({field: 'update me if you can'})
        self.assertError(ERROR_READONLY_FIELD % field)

    def test_unknown_data_type(self):
        field = 'name'
        value = 'catch_me'
        schema = {field: {'type': value}}
        self.assertSchemaError(self.document, schema, None,
                               ERROR_UNKNOWN_TYPE % (value, field))

    def test_not_a_string(self):
        self.assertBadType('a_required_string', 'string', 1)

    def test_not_a_integer(self):
        self.assertBadType('an_integer', 'integer', "i'm not an integer")

    def test_not_a_boolean(self):
        self.assertBadType('a_boolean', 'boolean', "i'm not an boolean")

    def test_not_a_datetime(self):
        self.assertBadType('a_datetime', 'datetime', "i'm not a datetime")

    def test_not_a_list(self):
        self.assertBadType('a_list_of_values', 'list', "i'm not a list")

    def test_not_a_dict(self):
        self.assertBadType('a_dict', 'dict', "i'm not a dict")

    def test_bad_max_length(self):
        field = 'a_required_string'
        max_length = self.schema[field]['maxlength']
        value = "".join(choice(lowercase) for i in range(max_length + 1))
        self.assertFail({field: value})
        self.assertError(ERROR_MAX_LENGTH % ('a_required_string', max_length))

    def test_bad_min_length(self):
        field = 'a_required_string'
        min_length = self.schema[field]['minlength']
        value = "".join(choice(lowercase) for i in range(min_length - 1))
        self.assertFail({field: value})
        self.assertError(ERROR_MIN_LENGTH % (field, min_length))

    def test_bad_max_value(self):
        field = 'an_integer'
        max_value = self.schema[field]['max']
        value = max_value + 1
        self.assertFail({field: value})
        self.assertError(ERROR_MAX_VALUE % (field, max_value))

    def test_bad_min_value(self):
        field = 'an_integer'
        min_value = self.schema[field]['min']
        value = min_value - 1
        self.assertFail({field: value})
        self.assertError(ERROR_MIN_VALUE % (field, min_value))

    def test_bad_schema(self):
        field = 'a_dict'
        schema_field = 'address'
        value = {schema_field: 34}
        self.assertFail({field: value})
        self.assertError("'%s': " % field + ERROR_BAD_TYPE %
                         (schema_field, 'string'))
        self.assertError("'%s': " % field + ERROR_REQUIRED_FIELD % 'city')

    def test_bad_list_of_values(self):
        field = 'a_list_of_values'
        value = ['a string', 'not an integer']
        self.assertFail({field: value})
        self.assertError("'%s': " % field + ERROR_BAD_TYPE %
                         ("_data1", 'integer'))

        value = ['a string', 10, 'an extra item']
        self.assertFail({field: value})
        self.assertError(ERROR_ITEMS_LIST % (field, 2))

    def test_bad_list_of_dicts(self):
        field = 'a_list_of_dicts'
        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        self.assertError("'%s': " % field + ERROR_BAD_TYPE %
                         ('price', 'integer'))

        value = ["not a dict"]
        self.assertValidationError({field: value}, None, None,
                                   ERROR_DOCUMENT_FORMAT % value[0])

    def test_validate_update(self):
        self.assertTrue(self.validator.validate_update({'an_integer': 100}))

    def test_string(self):
        self.assertSuccess({'a_required_string': 'john doe'})

    def test_integer(self):
        self.assertSuccess({'an_integer': 50})

    def test_boolean(self):
        self.assertSuccess({'a_boolean': True})

    def test_datetime(self):
        self.assertSuccess({'a_datetime': datetime.now()})

    def test_array(self):
        self.assertSuccess({'an_array': ['agent', 'client']})

    def tst_a_list_of_dicts(self):
        self.assertSuccess(
            {
                'a_list_of_dicts': [
                    {'sku': 'AK345', 'price': 100},
                    {'sku': 'YZ069', 'price': 25}
                ]
            }
        )

    def test_a_list_of_values(self):
        self.assertSuccess({'a_list_of_values': ['hello', 100]})

    def test_a_dict(self):
        self.assertSuccess(
            {
                'a_dict': {
                    'address': 'i live here',
                    'city': 'in my own town'
                }
            }
        )
