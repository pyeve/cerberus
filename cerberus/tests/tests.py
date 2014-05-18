import re
from datetime import datetime
from random import choice
from string import ascii_lowercase
from . import TestBase
from ..cerberus import Validator, errors, ValidationError
from ..mock import CerberusMock, CerberusKeySchemaMock


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
        self.assertError(field, errors.ERROR_UNKNOWN_FIELD)

    def test_unknown_rule(self):
        field = 'name'
        schema = {field: {'unknown_rule': True, 'type': 'string'}}
        self.assertSchemaError(
            self.document, schema, None,
            errors.ERROR_UNKNOWN_RULE % ('unknown_rule', field)
        )

    def test_required_field(self):
        self.assertFail({'an_integer': 1})
        self.assertError('a_required_string', errors.ERROR_REQUIRED_FIELD)

    def test_nullable_field(self):
        self.assertSuccess({'a_nullable_integer': None})
        self.assertSuccess({'a_nullable_integer': 3})
        self.assertSuccess({'a_nullable_field_without_type': None})
        self.assertFail({'a_nullable_integer': "foo"})
        self.assertFail({'an_integer': None})
        self.assertFail({'a_not_nullable_field_without_type': None})

    def test_readonly_field(self):
        field = 'a_readonly_string'
        self.assertFail({field: 'update me if you can'}, update=True)
        self.assertError(field, errors.ERROR_READONLY_FIELD)
        self.assertSuccess(
            {
                field: 'update me if you can',
                'a_required_string': 'required',  # for full re-validation
            },
            update=False)

    def test_unknown_data_type(self):
        field = 'name'
        value = 'catch_me'
        schema = {field: {'type': value}}
        self.assertSchemaError(self.document, schema, None,
                               errors.ERROR_UNKNOWN_TYPE % value)

    def test_not_a_string(self):
        self.assertBadType('a_required_string', 'string', 1)

    def test_not_a_integer(self):
        self.assertBadType('an_integer', 'integer', "i'm not an integer")

    def test_not_a_boolean(self):
        self.assertBadType('a_boolean', 'boolean', "i'm not an boolean")

    def test_not_a_datetime(self):
        self.assertBadType('a_datetime', 'datetime', "i'm not a datetime")

    def test_not_a_float(self):
        self.assertBadType('a_float', 'float', "i'm not a float")

    def test_not_a_number(self):
        self.assertBadType('a_number', 'number', "i'm not a number")

    def test_not_a_list(self):
        self.assertBadType('a_list_of_values', 'list', "i'm not a list")

    def test_not_a_dict(self):
        self.assertBadType('a_dict', 'dict', "i'm not a dict")

    def test_bad_max_length(self):
        field = 'a_required_string'
        max_length = self.schema[field]['maxlength']
        value = "".join(choice(ascii_lowercase) for i in range(max_length + 1))
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_MAX_LENGTH % max_length)

    def test_bad_min_length(self):
        field = 'a_required_string'
        min_length = self.schema[field]['minlength']
        value = "".join(choice(ascii_lowercase) for i in range(min_length - 1))
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_MIN_LENGTH % min_length)

    def test_bad_max_value(self):
        def assert_bad_max_value(field, inc):
            max_value = self.schema[field]['max']
            value = max_value + inc
            self.assertFail({field: value})
            self.assertError(field, errors.ERROR_MAX_VALUE % max_value)

        field = 'an_integer'
        assert_bad_max_value(field, 1)
        field = 'a_float'
        assert_bad_max_value(field, 1.0)
        field = 'a_number'
        assert_bad_max_value(field, 1)

    def test_bad_min_value(self):
        def assert_bad_min_value(field, inc):
            min_value = self.schema[field]['min']
            value = min_value - inc
            self.assertFail({field: value})
            self.assertError(field, errors.ERROR_MIN_VALUE % min_value)

        field = 'an_integer'
        assert_bad_min_value(field, 1)
        field = 'a_float'
        assert_bad_min_value(field, 1.0)
        field = 'a_number'
        assert_bad_min_value(field, 1)

    def test_bad_schema(self):
        field = 'a_dict'
        schema_field = 'address'
        value = {schema_field: 34}
        self.assertFail({field: value})
        v = self.validator
        self.assertTrue(field in v.errors)
        self.assertTrue(schema_field in v.errors[field])
        self.assertTrue(errors.ERROR_BAD_TYPE % 'string' in
                        v.errors[field][schema_field])
        self.assertTrue('city' in v.errors[field])
        self.assertTrue(errors.ERROR_REQUIRED_FIELD in
                        v.errors[field]['city'])

    def test_bad_keyschema(self):
        field = 'a_dict_with_keyschema'
        schema_field = 'a_string'
        value = {schema_field: 'not an integer'}
        self.assertFail({field: value})
        v = self.validator
        self.assertTrue(field in v.errors)
        self.assertTrue(schema_field in v.errors[field])
        self.assertTrue(errors.ERROR_BAD_TYPE % 'integer' in
                        v.errors[field][schema_field])

    def test_bad_list_of_values(self):
        field = 'a_list_of_values'
        value = ['a string', 'not an integer']
        self.assertFail({field: value})
        v = self.validator
        self.assertTrue(1 in v.errors)
        self.assertTrue(errors.ERROR_BAD_TYPE % 'integer' in
                        v.errors[1])

        value = ['a string', 10, 'an extra item']
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_ITEMS_LIST % 2)

    def test_bad_list_of_integers(self):
        field = 'a_list_of_integers'
        value = [34, 'not an integer']
        self.assertFail({field: value})

    def test_bad_list_of_dicts_deprecated(self):
        field = 'a_list_of_dicts_deprecated'
        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        self.assertError('price', errors.ERROR_BAD_TYPE % 'integer')

        value = ["not a dict"]
        self.assertValidationError({field: value}, None, None,
                                   errors.ERROR_DOCUMENT_FORMAT % value[0])

    def test_bad_list_of_dicts(self):
        field = 'a_list_of_dicts'
        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        v = self.validator
        self.assertTrue(field in v.errors)
        self.assertTrue(0 in v.errors[field])
        self.assertTrue('price' in v.errors[field][0])
        self.assertTrue(errors.ERROR_BAD_TYPE % 'integer' in
                        v.errors[field][0]['price'])

        value = ["not a dict"]
        self.assertValidationError({field: value}, None, None,
                                   errors.ERROR_DOCUMENT_FORMAT % value[0])

    def test_array_unallowed(self):
        field = 'an_array'
        value = ['agent', 'client', 'profit']
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_UNALLOWED_VALUES % ['profit'])

    def test_string_unallowed(self):
        field = 'a_restricted_string'
        value = 'profit'
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_UNALLOWED_VALUE % value)

    def test_integer_unallowed(self):
        field = 'a_restricted_integer'
        value = 2
        self.assertFail({field: value})
        self.assertError(field, errors.ERROR_UNALLOWED_VALUE % value)

    def test_integer_allowed(self):
        self.assertSuccess({'a_restricted_integer': -1})

    def test_validate_update(self):
        self.assertTrue(self.validator.validate({'an_integer': 100},
                                                update=True))

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

    def test_float(self):
        self.assertSuccess({'a_float': 3.5})

    def test_number(self):
        self.assertSuccess({'a_number': 3.5})
        self.assertSuccess({'a_number': 3})

    def test_array(self):
        self.assertSuccess({'an_array': ['agent', 'client']})

    def test_set(self):
        self.assertSuccess({'a_set': set(['hello', 1])})

    def test_regex(self):
        field = 'a_regex_email'
        self.assertSuccess({field: 'valid.email@gmail.com'})
        self.assertFalse(self.validator.validate({field: 'invalid'},
                                                 self.schema, update=True))
        self.assertError(field, 'does not match regex')

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

    def test_a_dict_with_keyschema(self):
        self.assertSuccess(
            {
                'a_dict_with_keyschema': {
                    'an integer': 99,
                    'another integer': 100
                }
            }
        )

    def test_a_list_length(self):
        field = 'a_list_length'
        min_length = self.schema[field]['minlength']
        max_length = self.schema[field]['maxlength']

        self.assertFail({field: [1] * (min_length - 1)})
        self.assertError(field, errors.ERROR_MIN_LENGTH % min_length)

        for i in range(min_length, max_length):
            value = [1] * i
            self.assertSuccess({field: value})

        self.assertFail({field: [1] * (max_length + 1)})
        self.assertError(field, errors.ERROR_MAX_LENGTH % max_length)

    def test_custom_datatype(self):
        class MyValidator(Validator):
            def _validate_type_objectid(self, field, value):
                if not re.match('[a-f0-9]{24}', value):
                    self._error(field, 'Not an ObjectId')

        schema = {'test_field': {'type': 'objectid'}}
        v = MyValidator(schema)
        self.assertTrue(v.validate({'test_field': '50ad188438345b1049c88a28'}))
        self.assertFalse(v.validate({'test_field': 'hello'}))
        self.assertError('test_field', 'Not an ObjectId', validator=v)

    def test_custom_datatype_rule(self):
        class MyValidator(Validator):
            def _validate_min_number(self, min_number, field, value):
                if value < min_number:
                    self._error(field, 'Below the min')

            def _validate_type_number(self, field, value):
                if not isinstance(value, int):
                    self._error(field, 'Not a number')

        schema = {'test_field': {'min_number': 1, 'type': 'number'}}
        v = MyValidator(schema)
        self.assertFalse(v.validate({'test_field': '0'}))
        self.assertError('test_field', 'Not a number', validator=v)
        self.assertFalse(v.validate({'test_field': 0}))
        self.assertError('test_field', 'Below the min', validator=v)

    def test_custom_validator(self):
        class MyValidator(Validator):
            def _validate_isodd(self, isodd, field, value):
                if isodd and not bool(value & 1):
                    self._error(field, 'Not an odd number')

        schema = {'test_field': {'isodd': True}}
        v = MyValidator(schema)
        self.assertTrue(v.validate({'test_field': 7}))
        self.assertFalse(v.validate({'test_field': 6}))
        self.assertError('test_field', 'Not an odd number', validator=v)

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
        self.assertError(field, errors.ERROR_EMPTY_NOT_ALLOWED)
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
        self.assertNoError(field, errors.ERROR_REQUIRED_FIELD, validator=v)

        # Test ignore None behaviour
        v = Validator(schema, ignore_none_values=True)
        schema[field]['required'] = False
        self.assertSuccess(schema=schema, document=document, validator=v)
        schema[field]['required'] = True
        self.assertFail(schema=schema, document=document, validator=v)
        self.assertError(field, errors.ERROR_REQUIRED_FIELD, validator=v)
        self.assertNoError(
            field,
            errors.ERROR_BAD_TYPE % 'string', validator=v
        )

    def test_unknown_keys(self):
        document = {"unknown1": True, "unknown2": "yes"}
        schema = {'a_field': {'type': 'string'}}
        v = Validator(allow_unknown=True)
        self.assertSuccess(schema=schema, document=document, validator=v)

    def test_novalidate_noerrors(self):
        '''In v0.1.0 and below `self.errors` raised an exception if no
        validation had been performed yet.
        '''
        self.assertEqual(self.validator.errors, {})

    def test_callable_validator(self):
        ''' Validator instance is callable, functions as a shorthand
        passthrough to validate()
        '''
        schema = {'test_field': {'type': 'string'}}
        v = Validator(schema)
        self.assertTrue(v.validate({'test_field': 'foo'}))
        self.assertTrue(v({'test_field': 'foo'}))
        self.assertFalse(v.validate({'test_field': 1}))
        self.assertFalse(v({'test_field': 1}))

    def test_dependencies_field(self):
        schema = {'test_field': {'dependencies': 'foo'}, 'foo': {'type':
                                                                 'string'}}
        v = Validator(schema)

        self.assertTrue(v.validate({'test_field': 'foobar', 'foo': 'bar'}))
        self.assertFalse(v.validate({'test_field': 'foobar'}))

    def test_dependencies_list(self):
        schema = {
            'test_field': {'dependencies': ['foo', 'bar']},
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        v = Validator(schema)

        self.assertTrue(v.validate({'test_field': 'foobar', 'foo': 'bar',
                                    'bar': 'foo'}))
        self.assertFalse(v.validate({'test_field': 'foobar', 'foo': 'bar'}))


class TestMock(TestBase):

    def test_blank_object(self):
        blank_object = CerberusMock(self.schema)
        self.assertEqual(blank_object, {'a_required_string': 'aa'})
        blank_object = CerberusMock(
            self.schema, create_missing=True, allow_unknown=True)
        expected = {
            'a_required_string': 'aa',
            'a_nullable_integer': None,
            'an_integer': 1,
            'a_restricted_integer': -1,
            'a_boolean': False,
            'a_datetime': datetime.fromtimestamp(0),
            'a_float': 1.0,
            'a_number': 1,
            'a_set': set(),
            'a_regex_email': 'a@a.a',
            'a_readonly_string': '',
            'a_restricted_string': 'agent',
            'an_array': [],
            'a_list_of_dicts_deprecated': [CerberusMock(schema={})],
            'a_list_of_dicts': [],
            'a_list_of_values': ['', 0],
            'a_list_of_integers': [],
            'a_dict': CerberusMock(
                schema=self.schema['a_dict']['schema'],
                document={'city': ''}),
            'a_dict_with_keyschema': CerberusKeySchemaMock(keyschema={
                'type': 'integer'}),
            'a_list_length': [0, 0],
            'a_nullable_field_without_type': None,
            'a_not_nullable_field_without_type': '',
        }
        self.assertEqual(blank_object, expected)
        self.assertTrue(isinstance(blank_object['a_dict'], CerberusMock))
        self.assertTrue(isinstance(
            blank_object['a_dict_with_keyschema'], CerberusKeySchemaMock))
        self.assertTrue(isinstance(
            blank_object['a_list_of_dicts_deprecated'][0], CerberusMock))

    def test_valid_initialisation(self):
        data = {
            'a_required_string': 'hello worl',
            'an_integer': 3}
        initialised_object = CerberusMock(self.schema, data)
        self.assertEqual(initialised_object, data)

    def test_invalid_initialisation(self):
        self.assertRaises(
            ValidationError, CerberusMock, self.schema, set(('an_integer', 3)))
        self.assertRaises(
            ValidationError, CerberusMock, self.schema, {
                'a_required_string': 'hello worl',
                'an_integer': 'not an integer'})

    def test_set_read_only(self):
        mock = CerberusMock(self.schema)
        self.assertRaises(
            ValidationError, mock.__setitem__,
            'a_readonly_string', 'new value')
        self.assertRaises(
            ValidationError, mock.update, {'a_readonly_string': 'new value'})

    def test_set_bad_value(self):
        mock = CerberusMock(self.schema)
        self.assertRaises(
            ValidationError, mock.__setitem__, 'a_dict',
            {'city': 'Reading', 'address': 300})

    def test_set_dict(self):
        mock = CerberusMock(self.schema)
        new_data = {'city': 'Reading', 'address': '300 Longwater Av'}
        mock['a_dict'] = new_data
        self.assertTrue(isinstance(mock['a_dict'], CerberusMock))
        self.assertEqual(mock['a_dict'], new_data)

    def test_set_list(self):
        mock = CerberusMock(self.schema)
        new_data = [{'sku': 'sounds like ska', 'price': 28}]
        mock['a_list_of_dicts'] = new_data
        self.assertTrue(isinstance(mock['a_list_of_dicts'][0], CerberusMock))
        self.assertEqual(mock['a_list_of_dicts'], new_data)

    def test_update(self):
        mock = CerberusMock(self.schema)
        new_data = {
            'a_set': set((1, 2, 3)),
            'an_array': ['agent', 'client', 'client'],
            'a_dict_with_keyschema': {'hello': 5}}
        mock.update(new_data)
        self.assertTrue(isinstance(
            mock['a_dict_with_keyschema'], CerberusKeySchemaMock))
        expected = {
            'a_required_string': 'aa',
            'a_set': set((1, 2, 3)),
            'an_array': ['agent', 'client', 'client'],
            'a_dict_with_keyschema': CerberusKeySchemaMock(
                keyschema={'type': 'integer'}, document={'hello': 5})}
        self.assertEqual(mock, expected)

    def test_delete_readonly_field(self):
        mock = CerberusMock(self.schema)
        # Mock not populated with value yet:
        self.assertRaises(KeyError, mock.__delitem__, 'a_readonly_string')
        mock = CerberusMock(
            self.schema, create_missing=True, allow_unknown=True)
        self.assertRaises(
            ValidationError, mock.__delitem__, 'a_readonly_string')

    def test_delete_required_field(self):
        mock = CerberusMock(self.schema)
        self.assertRaises(
            ValidationError, mock.__delitem__, 'a_required_string')


class TestKeySchemaMock(TestBase):
    def setUp(self):
        super(TestBase, self).setUp()
        self.mock = CerberusKeySchemaMock(keyschema={'type': 'integer'})

    def test_bad_setitem(self):
        self.assertRaises(
            ValidationError, self.mock.__setitem__, 'foo', 'hello world')

    def test_setitem(self):
        self.mock['foo'] = 3
        self.assertEqual(self.mock['foo'], 3)
