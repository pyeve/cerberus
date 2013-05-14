import re
from datetime import datetime
from random import choice
from string import ascii_lowercase
from . import TestBase
from ..cerberus import Validator, errors


class TestValidator(TestBase):

    def test_empty_schema(self):
        v = Validator()
        self.assertSchemaError(self.document, None, v,
                               errors.ERROR_SCHEMA_MISSING)

    def test_bad_schema_type(self):
        schema = "this string should really be  dict"
        v = Validator(schema)
        self.assertSchemaError(self.document, None, v,
                               errors.ERROR_SCHEMA_FORMAT % schema)

        v = Validator()
        self.assertSchemaError(self.document, schema, v,
                               errors.ERROR_SCHEMA_FORMAT % schema)

    def test_empty_document(self):
        self.assertValidationError(None, None, None,
                                   errors.ERROR_DOCUMENT_MISSING)

    def test_bad_document_type(self):
        document = "not a dict"
        self.assertValidationError(document, None, None,
                                   errors.ERROR_DOCUMENT_FORMAT % document)

    def test_bad_schema_definition(self):
        field = 'name'
        schema = {field: 'this should really be a dict'}
        self.assertSchemaError(self.document, schema, None,
                               errors.ERROR_DEFINITION_FORMAT % field)

    def test_unknown_field(self):
        field = 'surname'
        self.assertFail({field: 'doe'})
        self.assertError(errors.ERROR_UNKNOWN_FIELD % field)

    def test_unknown_rule(self):
        field = 'name'
        schema = {field: {'unknown_rule': True, 'type': 'string'}}
        self.assertSchemaError(
            self.document, schema, None,
            errors.ERROR_UNKNOWN_RULE % ('unknown_rule', field)
        )

    def test_required_field(self):
        self.assertFail({'an_integer': 1})
        self.assertError(errors.ERROR_REQUIRED_FIELD % 'a_required_string')

    def test_nullable_field_field(self):
        self.assertSuccess({'a_nullable_integer': None})
        self.assertSuccess({'a_nullable_integer': 3})
        self.assertFail({'a_nullable_integer': "foo"})
        self.assertFail({'an_integer': None})

    def test_readonly_field(self):
        field = 'a_readonly_string'
        self.assertFail({field: 'update me if you can'})
        self.assertError(errors.ERROR_READONLY_FIELD % field)

    def test_unknown_data_type(self):
        field = 'name'
        value = 'catch_me'
        schema = {field: {'type': value}}
        self.assertSchemaError(self.document, schema, None,
                               errors.ERROR_UNKNOWN_TYPE % (value, field))

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
        value = "".join(choice(ascii_lowercase) for i in range(max_length + 1))
        self.assertFail({field: value})
        self.assertError(
            errors.ERROR_MAX_LENGTH % ('a_required_string', max_length)
        )

    def test_bad_min_length(self):
        field = 'a_required_string'
        min_length = self.schema[field]['minlength']
        value = "".join(choice(ascii_lowercase) for i in range(min_length - 1))
        self.assertFail({field: value})
        self.assertError(errors.ERROR_MIN_LENGTH % (field, min_length))

    def test_bad_max_value(self):
        field = 'an_integer'
        max_value = self.schema[field]['max']
        value = max_value + 1
        self.assertFail({field: value})
        self.assertError(errors.ERROR_MAX_VALUE % (field, max_value))

    def test_bad_min_value(self):
        field = 'an_integer'
        min_value = self.schema[field]['min']
        value = min_value - 1
        self.assertFail({field: value})
        self.assertError(errors.ERROR_MIN_VALUE % (field, min_value))

    def test_bad_schema(self):
        field = 'a_dict'
        schema_field = 'address'
        value = {schema_field: 34}
        self.assertFail({field: value})
        self.assertError("'%s': " % field + errors.ERROR_BAD_TYPE %
                         (schema_field, 'string'))
        self.assertError(
            "'%s': " % field + errors.ERROR_REQUIRED_FIELD % 'city'
        )

    def test_bad_list_of_values(self):
        field = 'a_list_of_values'
        value = ['a string', 'not an integer']
        self.assertFail({field: value})
        self.assertError(
            errors.ERROR_BAD_TYPE % ("%s[%s]" % (field, 1), 'integer')
        )

        value = ['a string', 10, 'an extra item']
        self.assertFail({field: value})
        self.assertError(errors.ERROR_ITEMS_LIST % (field, 2))

    def test_bad_list_of_integers(self):
        field = 'a_list_of_integers'
        value = [34, 'not an integer']
        self.assertFail({field: value})
        self.assertError(
            errors.ERROR_BAD_TYPE % ("%s[%s]" % (field, 1), 'integer')
        )

    def test_bad_list_of_dicts_deprecated(self):
        field = 'a_list_of_dicts_deprecated'
        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        self.assertError("'%s': " % field + errors.ERROR_BAD_TYPE %
                         ('price', 'integer'))

        value = ["not a dict"]
        self.assertValidationError({field: value}, None, None,
                                   errors.ERROR_DOCUMENT_FORMAT % value[0])

    def test_bad_list_of_dicts(self):
        field = 'a_list_of_dicts'
        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        self.assertError("'%s[%s]': " % (field, 0) +
                         errors.ERROR_BAD_TYPE % ('price', 'integer'))

        value = ["not a dict"]
        self.assertValidationError({field: value}, None, None,
                                   errors.ERROR_DOCUMENT_FORMAT % value[0])

    def test_array_unallowed(self):
        field = 'an_array'
        value = ['agent', 'client', 'profit']
        self.assertFail({field: value})
        self.assertError(errors.ERROR_UNALLOWED_VALUES % (['profit'], field))

    def test_string_unallowed(self):
        field = 'a_restricted_string'
        value = 'profit'
        self.assertFail({field: value})
        self.assertError(errors.ERROR_UNALLOWED_VALUE % (value, field))

    def test_validate_update(self):
        self.assertTrue(self.validator.validate_update({'an_integer': 100}))

    def test_string(self):
        self.assertSuccess({'a_required_string': 'john doe'})

    def test_string_allowed(self):
        self.assertSuccess({'a_restricted_string': 'client'})

    def test_integer(self):
        self.assertSuccess({'an_integer': 50})

    def test_boolean(self):
        self.assertSuccess({'a_boolean': True})

    def test_datetime(self):
        self.assertSuccess({'a_datetime': datetime.now()})

    def test_array(self):
        self.assertSuccess({'an_array': ['agent', 'client']})

    def tst_a_list_of_dicts_deprecated(self):
        self.assertSuccess(
            {
                'a_list_of_dicts_deprecated': [
                    {'sku': 'AK345', 'price': 100},
                    {'sku': 'YZ069', 'price': 25}
                ]
            }
        )

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

    def test_a_list_of_integers(self):
        self.assertSuccess({'a_list_of_integers': [99, 100]})

    def test_a_dict(self):
        self.assertSuccess(
            {
                'a_dict': {
                    'address': 'i live here',
                    'city': 'in my own town'
                }
            }
        )

    def test_a_list_length(self):
        field = 'a_list_length'
        min_length = self.schema[field]['minlength']
        max_length = self.schema[field]['maxlength']

        self.assertFail({field: [1] * (min_length - 1)})
        self.assertError(errors.ERROR_MIN_LENGTH % (field, min_length))

        for i in range(min_length, max_length):
            value = [1] * i
            self.assertSuccess({field: value})

        self.assertFail({field: [1] * (max_length + 1)})
        self.assertError(errors.ERROR_MAX_LENGTH % (field, max_length))

    def test_custom_datatype(self):
        class MyValidator(Validator):
            def _validate_type_objectid(self, field, value):
                if not re.match('[a-f0-9]{24}', value):
                    self._error('Not an ObjectId')

        schema = {'test_field': {'type': 'objectid'}}
        v = MyValidator(schema)
        self.assertTrue(v.validate({'test_field': '50ad188438345b1049c88a28'}))
        self.assertFalse(v.validate({'test_field': 'hello'}))
        self.assertError('Not an ObjectId', validator=v)

    def test_custom_validator(self):
        class MyValidator(Validator):
            def _validate_isodd(self, isodd, field, value):
                if isodd and not bool(value & 1):
                    self._error('Not an odd number')

        schema = {'test_field': {'isodd': True}}
        v = MyValidator(schema)
        self.assertTrue(v.validate({'test_field': 7}))
        self.assertFalse(v.validate({'test_field': 6}))
        self.assertError('Not an odd number', validator=v)

    def test_transparent_schema_rules(self):
        field = 'test'
        schema = {field: {'type': 'string', 'unknown_rule': 'a value'}}
        document = {field: 'hey!'}
        v = Validator(transparent_schema_rules=True)
        self.assertSuccess(schema=schema, document=document, validator=v)
        v.transparent_schema_rules = False
        self.assertSchemaError(
            document, schema, v,
            errors.ERROR_UNKNOWN_RULE % ('unknown_rule', field)
        )
        self.assertSchemaError(
            document, schema, None,
            errors.ERROR_UNKNOWN_RULE % ('unknown_rule', field)
        )

    def test_allow_empty_strings(self):
        field = 'test'
        schema = {field: {'type': 'string'}}
        document = {field: ''}
        self.assertSuccess(document, schema)
        schema[field]['empty'] = False
        self.assertFail(document, schema)
        self.assertError(errors.ERROR_EMPTY_NOT_ALLOWED % field)
        schema[field]['empty'] = True
        self.assertSuccess(document, schema)

    def test_ignore_none_values(self):
        field = 'test'
        schema = {field: {'type': 'string', 'empty': False, 'required': False}}
        document = {field: None}
        # Test normal behaviour
        v = Validator(schema, ignore_none_values=False)
        self.assertFail(schema=schema, document=document, validator=v)
        schema[field]['required'] = True
        self.assertFail(schema=schema, document=document, validator=v)
        self.assertNotError(errors.ERROR_REQUIRED_FIELD % (field), validator=v)
        # Test ignore None behaviour
        v = Validator(schema, ignore_none_values=True)
        schema[field]['required'] = False
        self.assertSuccess(schema=schema, document=document, validator=v)
        schema[field]['required'] = True
        self.assertFail(schema=schema, document=document, validator=v)
        self.assertError(errors.ERROR_REQUIRED_FIELD % (field), validator=v)
        self.assertNotError(
            errors.ERROR_BAD_TYPE % (field, 'string'), validator=v
        )

    def test_unknown_keys(self):
        document = {"unknown1": True, "unknown2": "yes"}
        schema = {'a_field': {'type': 'string'}}
        v = Validator(allow_unknown=True)
        self.assertSuccess(schema=schema, document=document, validator=v)
