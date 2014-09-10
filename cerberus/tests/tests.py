import re
from datetime import datetime
from random import choice
from string import ascii_lowercase
from . import TestBase
from ..cerberus import Validator, errors, SchemaError


class TestValidator(TestBase):

    def test_empty_schema(self):
        v = Validator()
        self.assertSchemaError(self.document, None, v,
                               errors.ERROR_SCHEMA_MISSING)

    def test_bad_schema_type(self):
        schema = "this string should really be dict"
        try:
            Validator(schema)
        except SchemaError as e:
            self.assertEqual(str(e), errors.ERROR_SCHEMA_FORMAT % schema)
        else:
            self.fail('SchemaError not raised')

        v = Validator()
        self.assertSchemaError(self.document, schema, v,
                               errors.ERROR_SCHEMA_FORMAT % schema)

    def _check_schema_content_error(self, err_msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except SchemaError as e:
            self.assertTrue(err_msg in str(e))
        else:
            self.fail('SchemaError not raised')

    def test_invalid_schema(self):
        schema = {'foo': {'unknown': 'rule'}}
        err_msg = ' '.join(errors.ERROR_UNKNOWN_RULE.split()[:2])
        self._check_schema_content_error(err_msg, Validator, schema)
        v = Validator()
        self._check_schema_content_error(
            err_msg, v.validate, {}, schema=schema)

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

    def test_empty_field_definition(self):
        field = 'name'
        schema = {field: {}}
        self.assertSuccess(self.document, schema)

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
        self.assertFail({field: 'update me if you can'})
        self.assertError(field, errors.ERROR_READONLY_FIELD)

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
        self.assertSuccess({'a_float': 1})

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
        schema = {}

        # test that unknown fields are allowed when allow_unknown is True.
        v = Validator(allow_unknown=True, schema=schema)
        self.assertSuccess({"unknown1": True, "unknown2": "yes"}, validator=v)

        # test that unknown fields are allowed only if they meet the
        # allow_unknown schema when provided.
        v.allow_unknown = {'type': 'string'}
        self.assertSuccess(document={'name': 'mark'}, validator=v)
        self.assertFail({"name": 1}, validator=v)

        # test that unknown fields are not allowed if allow_unknown is False
        v.allow_unknown = False
        self.assertFail({'name': 'mark'}, validator=v)

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

    def test_dependencies_with_required_field(self):
        schema = {
            'test_field': {'required': True, 'dependencies': ['foo', 'bar']},
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        v = Validator(schema)

        # False: all dependencies missing
        self.assertFalse(v.validate({'test_field': 'foobar'}))

        # False: one of dependencies missing
        self.assertFalse(v.validate({'test_field': 'foobar', 'foo': 'bar'}))

        # False: dependencies are validated and field is required
        self.assertFalse(v.validate({'foo': 'bar', 'bar': 'foo'}))

        # True: All dependencies are optional
        # so do not check the field if dependencies do not exist
        self.assertTrue(v.validate({}))

        # True: dependency missing
        self.assertTrue(v.validate({'foo': 'bar'}))

        # True: dependencies are validated but field is not required
        schema['test_field']['required'] = False
        self.assertTrue(v.validate({'foo': 'bar', 'bar': 'foo'}))

    def test_options_passed_to_nested_validators(self):
        schema = {'sub_dict': {'type': 'dict',
                               'schema': {'foo': {'type': 'string'}}}}
        v = Validator(schema, allow_unknown=True)
        self.assertTrue(v.validate({'sub_dict': {'foo': 'bar',
                                                 'unknown': True}}))

    def test_self_document_always_root(self):
        ''' Make sure self.document is always the root document.
        See:
        * https://github.com/nicolaiarocci/cerberus/pull/42
        * https://github.com/nicolaiarocci/eve/issues/295
        '''
        class MyValidator(Validator):
            def _validate_root_doc(self, root_doc, field, value):
                if('sub' not in self.document or
                        len(self.document['sub']) != 2):
                    self._error(field, 'self.document is not the root doc!')

        schema = {
            'sub': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'root_doc': True,
                    'schema': {
                        'foo': {
                            'type': 'string',
                            'root_doc': True
                        }
                    }
                }
            }
        }
        v = MyValidator(schema)

        obj = {'sub': [{'foo': 'bar'}, {'foo': 'baz'}]}
        self.assertTrue(v.validate(obj))

    def test_validator_rule(self):
        def validate_name(field, value, error):
            if not value.islower():
                error(field, 'must be lowercase')

        schema = {
            'name': {'validator': validate_name},
            'age': {'type': 'integer'}
        }
        v = Validator(schema)

        self.assertFail({'name': 'ItsMe', 'age': 2}, validator=v)
        self.assertError('name', 'must be lowercase', validator=v)

        self.assertSuccess({'name': 'itsme', 'age': 2}, validator=v)
