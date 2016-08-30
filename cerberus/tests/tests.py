# -*- coding: utf-8 -*-

from datetime import date, datetime
from random import choice
import re
from string import ascii_lowercase
from tempfile import NamedTemporaryFile

if __name__ == '__main__':
    import os
    import sys
    import unittest  # TODO pytest
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..', '..')))

from cerberus import (schema_registry, rules_set_registry, SchemaError,
                      Validator, errors)  # noqa
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


class TestValidation(TestBase):
    def test_empty_document(self):
        self.assertValidationError(None, None, None,
                                   errors.DOCUMENT_MISSING)

    def test_bad_document_type(self):
        document = "not a dict"
        self.assertValidationError(
            document, None, None, errors.DOCUMENT_FORMAT.format(
                document)
        )

    def test_unknown_field(self):
        field = 'surname'
        self.assertFail({field: 'doe'})
        self.assertError(field, (), errors.UNKNOWN_FIELD, None)
        self.assertDictEqual(self.validator.errors, {field: ['unknown field']})

    def test_empty_field_definition(self):
        field = 'name'
        schema = {field: {}}
        self.assertSuccess(self.document, schema)

    def test_required_field(self):
        field = 'a_required_string'
        self.schema.update(self.required_string_extension)
        self.assertFail({'an_integer': 1}, self.schema)
        self.assertError(field, (field, 'required'), errors.REQUIRED_FIELD,
                         True)

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
        self.assertError(field, (field, 'readonly'), errors.READONLY_FIELD,
                         True)

    def test_readonly_field_first_rule(self):
        # test that readonly rule is checked before any other rule, and blocks.
        # See #63.
        schema = {
            'a_readonly_number': {
                'type': 'integer',
                'readonly': True,
                'max': 1
            }
        }
        v = Validator(schema)
        v.validate({'a_readonly_number': 2})
        # it would be a list if there's more than one error; we get a dict
        # instead.
        self.assertIn('read-only', v.errors['a_readonly_number'][0])

    def test_not_a_string(self):
        self.assertBadType('a_string', 'string', 1)

    def test_not_a_binary(self):
        # 'u' literal prefix produces type `str` in Python 3
        self.assertBadType('a_binary', 'binary', u"i'm not a binary")

    def test_not_a_integer(self):
        self.assertBadType('an_integer', 'integer', "i'm not an integer")

    def test_not_a_boolean(self):
        self.assertBadType('a_boolean', 'boolean', "i'm not a boolean")

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
        field = 'a_string'
        max_length = self.schema[field]['maxlength']
        value = "".join(choice(ascii_lowercase) for i in range(max_length + 1))
        self.assertFail({field: value})
        self.assertError(field, (field, 'maxlength'), errors.MAX_LENGTH,
                         max_length, (len(value),))

    def test_bad_max_length_binary(self):
        field = 'a_binary'
        max_length = self.schema[field]['maxlength']
        value = b'\x00' * (max_length + 1)
        self.assertFail({field: value})
        self.assertError(field, (field, 'maxlength'), errors.MAX_LENGTH,
                         max_length, (len(value),))

    def test_bad_min_length(self):
        field = 'a_string'
        min_length = self.schema[field]['minlength']
        value = "".join(choice(ascii_lowercase) for i in range(min_length - 1))
        self.assertFail({field: value})
        self.assertError(field, (field, 'minlength'), errors.MIN_LENGTH,
                         min_length, (len(value),))

    def test_bad_min_length_binary(self):
        field = 'a_binary'
        min_length = self.schema[field]['minlength']
        value = b'\x00' * (min_length - 1)
        self.assertFail({field: value})
        self.assertError(field, (field, 'minlength'), errors.MIN_LENGTH,
                         min_length, (len(value),))

    def test_bad_max_value(self):
        def assert_bad_max_value(field, inc):
            max_value = self.schema[field]['max']
            value = max_value + inc
            self.assertFail({field: value})
            self.assertError(field, (field, 'max'), errors.MAX_VALUE,
                             max_value)

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
            self.assertError(field, (field, 'min'), errors.MIN_VALUE,
                             min_value)

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
        self.assertError((field, schema_field),
                         (field, 'schema', schema_field, 'type'),
                         errors.BAD_TYPE, 'string')

        v = self.validator
        handler = errors.BasicErrorHandler
        self.assertIn(field, v.errors)
        self.assertIn(schema_field, v.errors[field][-1])
        self.assertIn(handler.messages[errors.BAD_TYPE.code]
                      .format(constraint='string'),
                      v.errors[field][-1][schema_field])
        self.assertIn('city', v.errors[field][-1])
        self.assertIn(handler.messages[errors.REQUIRED_FIELD.code],
                      v.errors[field][-1]['city'])

    def test_bad_valueschema(self):
        field = 'a_dict_with_valueschema'
        schema_field = 'a_string'
        value = {schema_field: 'not an integer'}
        self.assertFail({field: value})

        exp_child_errors = [((field, schema_field), (field, 'valueschema',
                             'type'), errors.BAD_TYPE, 'integer')]
        self.assertChildErrors(field, (field, 'valueschema'), errors.VALUESCHEMA,  # noqa
                               {'type': 'integer'}, child_errors=exp_child_errors)  # noqa

    def test_bad_list_of_values(self):
        field = 'a_list_of_values'
        value = ['a string', 'not an integer']
        self.assertFail({field: value})
        self.assertChildErrors(field, (field, 'items'), errors.BAD_ITEMS,
                               [{'type': 'string'}, {'type': 'integer'}],
                               child_errors=[
                                   ((field, 1), (field, 'items', 1, 'type'),
                                    errors.BAD_TYPE, 'integer')])
        self.assertIn(errors.BasicErrorHandler.messages[errors.BAD_TYPE.code].
                      format(constraint='integer'),
                      self.validator.errors[field][-1][1])

        value = ['a string', 10, 'an extra item']
        self.assertFail({field: value})
        self.assertError(field, (field, 'items'), errors.ITEMS_LENGTH,
                         [{'type': 'string'}, {'type': 'integer'}], (2, 3))

    def test_bad_list_of_integers(self):
        field = 'a_list_of_integers'
        value = [34, 'not an integer']
        self.assertFail({field: value})

    def test_bad_list_of_dicts(self):
        field = 'a_list_of_dicts'
        subschema = self.schema['a_list_of_dicts']['schema']

        value = [{'sku': 'KT123', 'price': '100'}]
        self.assertFail({field: value})
        exp_child_errors = [((field, 0, 'price'),
                            (field, 'schema', 'schema', 'price', 'type'),
                             errors.BAD_TYPE, 'integer')]
        self.assertChildErrors(field, (field, 'schema'),
                               errors.SEQUENCE_SCHEMA, subschema,
                               child_errors=exp_child_errors)

        v = self.validator
        self.assertIn(field, v.errors)
        self.assertIn(0, v.errors[field][-1])
        self.assertIn('price', v.errors[field][-1][0][-1])
        exp_msg = errors.BasicErrorHandler.messages[errors.BAD_TYPE.code]\
            .format(constraint='integer')
        self.assertIn(exp_msg, v.errors[field][-1][0][-1]['price'])

        value = ["not a dict"]
        self.assertFail({field: value})
        exp_child_errors = [((field, 0), (field, 'schema', 'type'),
                             errors.BAD_TYPE, 'dict', ())]
        self.assertChildErrors(field, (field, 'schema'),
                               errors.SEQUENCE_SCHEMA, subschema,
                               child_errors=exp_child_errors)

    def test_array_unallowed(self):
        field = 'an_array'
        value = ['agent', 'client', 'profit']
        self.assertFail({field: value})
        self.assertError(field, (field, 'allowed'), errors.UNALLOWED_VALUES,
                         ['agent', 'client', 'vendor'], ['profit'])

    def test_string_unallowed(self):
        field = 'a_restricted_string'
        value = 'profit'
        self.assertFail({field: value})
        self.assertError(field, (field, 'allowed'), errors.UNALLOWED_VALUE,
                         ['agent', 'client', 'vendor'], value)

    def test_integer_unallowed(self):
        field = 'a_restricted_integer'
        value = 2
        self.assertFail({field: value})
        self.assertError(field, (field, 'allowed'), errors.UNALLOWED_VALUE,
                         [-1, 0, 1], value)

    def test_integer_allowed(self):
        self.assertSuccess({'a_restricted_integer': -1})

    def test_validate_update(self):
        self.assertSuccess({'an_integer': 100,
                            'a_dict': {'address': 'adr'},
                            'a_list_of_dicts': [{'sku': 'let'}]
                            }, update=True)

    def test_string(self):
        self.assertSuccess({'a_string': 'john doe'})

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

    def test_one_of_two_types(self):
        field = 'one_or_more_strings'
        self.assertSuccess({field: 'foo'})
        self.assertSuccess({field: ['foo', 'bar']})
        self.assertFail({field: 23})
        self.assertError((field,), (field, 'type'), errors.BAD_TYPE,
                         ['string', 'list'])
        self.assertFail({field: ['foo', 23]})
        exp_child_errors = [((field, 1), (field, 'schema', 'type'),
                             errors.BAD_TYPE, 'string')]
        self.assertChildErrors(field, (field, 'schema'),
                               errors.SEQUENCE_SCHEMA, {'type': 'string'},
                               child_errors=exp_child_errors)
        self.assertDictEqual(self.validator.errors,
                             {field: [{1: ['must be of string type']}]})

    def test_regex(self):
        field = 'a_regex_email'
        self.assertSuccess({field: 'valid.email@gmail.com'})
        self.assertFail({field: 'invalid'}, self.schema, update=True)
        self.assertError(field, (field, 'regex'), errors.REGEX_MISMATCH,
                         '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    def test_a_list_of_dicts(self):
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
        self.assertSuccess({'a_dict': {'address': 'i live here',
                                       'city': 'in my own town'}})
        self.assertFail({'a_dict': {'address': 8545}})
        self.assertErrors([
            (('a_dict', 'address'), ('a_dict', 'schema', 'address', 'type'),
             errors.BAD_TYPE, 'string'),
            (('a_dict', 'city'), ('a_dict', 'schema', 'city', 'required'),
             errors.REQUIRED_FIELD, True)
        ])

    def test_a_dict_with_valueschema(self):
        self.assertSuccess(
            {'a_dict_with_valueschema':
                {'an integer': 99, 'another integer': 100}})

        self.assertFail({'a_dict_with_valueschema': {'a string': '99'}})
        self.assertChildErrors(
            'a_dict_with_valueschema',
            ('a_dict_with_valueschema', 'valueschema'),
            errors.VALUESCHEMA, {'type': 'integer'}, child_errors=[
                (('a_dict_with_valueschema', 'a string'),
                 ('a_dict_with_valueschema', 'valueschema', 'type'),
                 errors.BAD_TYPE, 'integer')])
        self.assertIn('valueschema', self.validator.schema_error_tree
                      ['a_dict_with_valueschema'])
        self.assertEqual(len(self.validator.schema_error_tree
                             ['a_dict_with_valueschema']['valueschema']
                             .descendants), 1)

    def test_a_dict_with_keyschema(self):
        self.assertSuccess(
            {
                'a_dict_with_keyschema': {
                    'key': 'value'
                }
            }
        )

        self.assertFail(
            {
                'a_dict_with_keyschema': {
                    'KEY': 'value'
                }
            }
        )

    def test_a_list_length(self):
        field = 'a_list_length'
        min_length = self.schema[field]['minlength']
        max_length = self.schema[field]['maxlength']

        self.assertFail({field: [1] * (min_length - 1)})
        self.assertError(field, (field, 'minlength'), errors.MIN_LENGTH,
                         min_length, (min_length - 1,))

        for i in range(min_length, max_length):
            value = [1] * i
            self.assertSuccess({field: value})

        self.assertFail({field: [1] * (max_length + 1)})
        self.assertError(field, (field, 'maxlength'), errors.MAX_LENGTH,
                         max_length, (max_length + 1,))

    def test_custom_datatype(self):
        class MyValidator(Validator):
            def _validate_type_objectid(self, value):
                if re.match('[a-f0-9]{24}', value):
                    return True

        schema = {'test_field': {'type': 'objectid'}}
        v = MyValidator(schema)
        self.assertSuccess({'test_field': '50ad188438345b1049c88a28'},
                           validator=v)
        self.assertFail({'test_field': 'hello'}, validator=v)
        self.assertError('test_field', ('test_field', 'type'), errors.BAD_TYPE,
                         'objectid', v_errors=v._errors)

    def test_custom_datatype_rule(self):
        class MyValidator(Validator):
            def _validate_min_number(self, min_number, field, value):
                """ {'type': 'number'} """
                if value < min_number:
                    self._error(field, 'Below the min')

            def _validate_type_number(self, value):
                if isinstance(value, int):
                    return True

        schema = {'test_field': {'min_number': 1, 'type': 'number'}}
        v = MyValidator(schema)
        self.assertFail({'test_field': '0'}, validator=v)
        self.assertError('test_field', ('test_field', 'type'), errors.BAD_TYPE,
                         'number', v_errors=v._errors)
        self.assertFail({'test_field': 0}, validator=v)
        self.assertError('test_field', (), errors.CUSTOM, None,
                         ('Below the min',), v_errors=v._errors)
        self.assertDictEqual(v.errors, {'test_field': ['Below the min']})

    def test_custom_validator(self):
        class MyValidator(Validator):
            def _validate_isodd(self, isodd, field, value):
                """ {'type': 'boolean'} """
                if isodd and not bool(value & 1):
                    self._error(field, 'Not an odd number')

        schema = {'test_field': {'isodd': True}}
        v = MyValidator(schema)
        self.assertSuccess({'test_field': 7}, validator=v)
        self.assertFail({'test_field': 6}, validator=v)
        self.assertError('test_field', (), errors.CUSTOM, None,
                         ('Not an odd number',), v_errors=v._errors)
        self.assertDictEqual(v.errors, {'test_field': ['Not an odd number']})

    def test_allow_empty_strings(self):
        field = 'test'
        schema = {field: {'type': 'string'}}
        document = {field: ''}
        self.assertSuccess(document, schema)
        schema[field]['empty'] = False
        self.assertFail(document, schema)
        self.assertError(field, (field, 'empty'), errors.EMPTY_NOT_ALLOWED,
                         False)
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
        self.assertNoError(field, (field, 'required'), errors.REQUIRED_FIELD,
                           True, v_errors=v._errors)

        # Test ignore None behaviour
        v = Validator(schema, ignore_none_values=True)
        schema[field]['required'] = False
        self.assertSuccess(schema=schema, document=document, validator=v)
        schema[field]['required'] = True
        self.assertFail(schema=schema, document=document, validator=v)
        self.assertError(field, (field, 'required'), errors.REQUIRED_FIELD,
                         True, v_errors=v._errors)
        self.assertNoError(field, (field, 'type'), errors.BAD_TYPE, 'string',
                           v_errors=v._errors)

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

    def test_unknown_key_dict(self):
        # https://github.com/nicolaiarocci/cerberus/issues/177
        self.validator.allow_unknown = True
        document = {'a_dict': {'foo': 'foo_value', 'bar': 25}}

        self.assertSuccess(document, {})

    def test_unknown_key_list(self):
        # https://github.com/nicolaiarocci/cerberus/issues/177
        self.validator.allow_unknown = True
        document = {'a_dict': ['foo', 'bar']}

        self.assertSuccess(document, {})

    def test_unknown_keys_list_of_dicts(self):
        # test that allow_unknown is honored even for subdicts in lists.
        # See 67.
        self.validator.allow_unknown = True
        document = {'a_list_of_dicts': [{'sku': 'YZ069', 'price': 25,
                                         'extra': True}]}

        self.assertSuccess(document)

    def test_unknown_keys_retain_custom_rules(self):
        # test that allow_unknown schema respect custom validation rules.
        # See #66.
        class CustomValidator(Validator):
            def _validate_type_foo(self, value):
                if value == "foo":
                    return True

        v = CustomValidator({})
        v.allow_unknown = {"type": "foo"}
        self.assertSuccess(document={"fred": "foo", "barney": "foo"},
                           validator=v)

    def test_nested_unknown_keys(self):
        schema = {
            'field1': {
                'type': 'dict',
                'allow_unknown': True,
                'schema': {'nested1': {'type': 'string'}}
            }
        }
        document = {
            'field1': {
                'nested1': 'foo',
                'arb1': 'bar',
                'arb2': 42
            }
        }
        self.assertSuccess(document=document, schema=schema)

        schema['field1']['allow_unknown'] = {'type': 'string'}
        self.assertFail(document=document, schema=schema)

    def test_novalidate_noerrors(self):
        """
        In v0.1.0 and below `self.errors` raised an exception if no
        validation had been performed yet.
        """
        self.assertEqual(self.validator.errors, {})

    def test_callable_validator(self):
        """
        Validator instance is callable, functions as a shorthand
        passthrough to validate()
        """
        schema = {'test_field': {'type': 'string'}}
        v = Validator(schema)
        self.assertTrue(v.validate({'test_field': 'foo'}))
        self.assertTrue(v({'test_field': 'foo'}))
        self.assertFalse(v.validate({'test_field': 1}))
        self.assertFalse(v({'test_field': 1}))

    def test_dependencies_field(self):
        schema = {'test_field': {'dependencies': 'foo'},
                  'foo': {'type': 'string'}}
        self.assertSuccess({'test_field': 'foobar', 'foo': 'bar'}, schema)
        self.assertFail({'test_field': 'foobar'}, schema)

    def test_dependencies_list(self):
        schema = {
            'test_field': {'dependencies': ['foo', 'bar']},
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        self.assertSuccess({'test_field': 'foobar', 'foo': 'bar', 'bar': 'foo'},  # noqa
                           schema)
        self.assertFail({'test_field': 'foobar', 'foo': 'bar'}, schema)

    def test_dependencies_list_with_required_field(self):
        schema = {
            'test_field': {'required': True, 'dependencies': ['foo', 'bar']},
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        # False: all dependencies missing
        self.assertFail({'test_field': 'foobar'}, schema)
        # False: one of dependencies missing
        self.assertFail({'test_field': 'foobar', 'foo': 'bar'}, schema)
        # False: one of dependencies missing
        self.assertFail({'test_field': 'foobar', 'bar': 'foo'}, schema)
        # False: dependencies are validated and field is required
        self.assertFail({'foo': 'bar', 'bar': 'foo'}, schema)
        # Flase: All dependencies are optional but field is still required
        self.assertFail({}, schema)
        # True: dependency missing
        self.assertFail({'foo': 'bar'}, schema)
        # True: dependencies are validated but field is not required
        schema['test_field']['required'] = False
        self.assertSuccess({'foo': 'bar', 'bar': 'foo'}, schema)

    def test_dependencies_list_with_subodcuments_fields(self):
        schema = {
            'test_field': {'dependencies': ['a_dict.foo', 'a_dict.bar']},
            'a_dict': {
                'type': 'dict',
                'schema': {
                    'foo': {'type': 'string'},
                    'bar': {'type': 'string'}
                }
            }
        }
        self.assertSuccess({'test_field': 'foobar',
                            'a_dict': {'foo': 'foo', 'bar': 'bar'}}, schema)
        self.assertFail({'test_field': 'foobar', 'a_dict': {}}, schema)
        self.assertFail({'test_field': 'foobar',
                         'a_dict': {'foo': 'foo'}}, schema)

    def test_dependencies_dict(self):
        schema = {
            'test_field': {'dependencies': {'foo': 'foo', 'bar': 'bar'}},
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        self.assertSuccess({'test_field': 'foobar', 'foo': 'foo', 'bar': 'bar'},  # noqa
                           schema)
        self.assertFail({'test_field': 'foobar', 'foo': 'foo'}, schema)
        self.assertFail({'test_field': 'foobar', 'foo': 'bar'}, schema)
        self.assertFail({'test_field': 'foobar', 'bar': 'bar'}, schema)
        self.assertFail({'test_field': 'foobar', 'bar': 'foo'}, schema)
        self.assertFail({'test_field': 'foobar'}, schema)

    def test_dependencies_dict_with_required_field(self):
        schema = {
            'test_field': {
                'required': True,
                'dependencies': {'foo': 'foo', 'bar': 'bar'}
            },
            'foo': {'type': 'string'},
            'bar': {'type': 'string'}
        }
        # False: all dependencies missing
        self.assertFail({'test_field': 'foobar'}, schema)
        # False: one of dependencies missing
        self.assertFail({'test_field': 'foobar', 'foo': 'foo'}, schema)
        self.assertFail({'test_field': 'foobar', 'bar': 'bar'}, schema)
        # False: dependencies are validated and field is required
        self.assertFail({'foo': 'foo', 'bar': 'bar'}, schema)
        # False: All dependencies are optional, but field is still required
        self.assertFail({}, schema)
        # False: dependency missing
        self.assertFail({'foo': 'bar'}, schema)

        self.assertSuccess({'test_field': 'foobar', 'foo': 'foo', 'bar': 'bar'},  # noqa
                           schema)

        # True: dependencies are validated but field is not required
        schema['test_field']['required'] = False
        self.assertSuccess({'foo': 'bar', 'bar': 'foo'}, schema)

    def test_dependencies_dict_with_subodcuments_fields(self):
        schema = {
            'test_field': {'dependencies': {'a_dict.foo': ['foo', 'bar'],
                                            'a_dict.bar': 'bar'}},
            'a_dict': {
                'type': 'dict',
                'schema': {
                    'foo': {'type': 'string'},
                    'bar': {'type': 'string'}
                }
            }
        }
        self.assertSuccess({'test_field': 'foobar',
                            'a_dict': {'foo': 'foo', 'bar': 'bar'}}, schema)
        self.assertSuccess({'test_field': 'foobar',
                            'a_dict': {'foo': 'bar', 'bar': 'bar'}}, schema)
        self.assertFail({'test_field': 'foobar', 'a_dict': {}}, schema)
        self.assertFail({'test_field': 'foobar',
                         'a_dict': {'foo': 'foo', 'bar': 'foo'}}, schema)
        self.assertFail({'test_field': 'foobar', 'a_dict': {'bar': 'foo'}},
                        schema)
        self.assertFail({'test_field': 'foobar', 'a_dict': {'bar': 'bar'}},
                        schema)

    def test_dependencies_errors(self):
        v = Validator({'field1': {'required': False},
                       'field2': {'required': True,
                                  'dependencies': {'field1': ['one', 'two']}}})
        v.validate({'field1': 'three', 'field2': 7})
        self.assertError('field2', ('field2', 'dependencies'),
                         errors.DEPENDENCIES_FIELD_VALUE,
                         {'field1': ['one', 'two']}, ({'field1': 'three'}, ),
                         v_errors=v._errors)

    def test_options_passed_to_nested_validators(self):
        schema = {'sub_dict': {'type': 'dict',
                               'schema': {'foo': {'type': 'string'}}}}
        v = Validator(schema, allow_unknown=True)
        self.assertSuccess({'sub_dict': {'foo': 'bar', 'unknown': True}},
                           validator=v)

    def test_self_root_document(self):
        """ Make sure self.root_document is always the root document.
        See:
        * https://github.com/nicolaiarocci/cerberus/pull/42
        * https://github.com/nicolaiarocci/eve/issues/295
        """
        class MyValidator(Validator):
            def _validate_root_doc(self, root_doc, field, value):
                """ {'type': 'boolean'} """
                if('sub' not in self.root_document or
                        len(self.root_document['sub']) != 2):
                    self._error(field, 'self.context is not the root doc!')

        schema = {
            'sub': {
                'type': 'list',
                'root_doc': True,
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'foo': {
                            'type': 'string',
                            'root_doc': True
                        }
                    }
                }
            }
        }
        self.assertSuccess({'sub': [{'foo': 'bar'}, {'foo': 'baz'}]},
                           validator=MyValidator(schema))

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
        self.assertError('name', (), errors.CUSTOM, None,
                         ('must be lowercase',), v_errors=v._errors)
        self.assertDictEqual(v.errors, {'name': ['must be lowercase']})
        self.assertSuccess({'name': 'itsme', 'age': 2}, validator=v)

    def test_validated(self):
        schema = {'property': {'type': 'string'}}
        v = Validator(schema)
        document = {'property': 'string'}
        self.assertEqual(v.validated(document), document)
        document = {'property': 0}
        self.assertIsNone(v.validated(document))

    def test_anyof(self):
        # prop1 must be either a number between 0 and 10
        schema = {'prop1': {'min': 0, 'max': 10}}
        doc = {'prop1': 5}

        self.assertSuccess(doc, schema)

        # prop1 must be either a number between 0 and 10 or 100 and 110
        schema = {'prop1':
                  {'anyof':
                   [{'min': 0, 'max': 10}, {'min': 100, 'max': 110}]}}
        doc = {'prop1': 105}

        self.assertSuccess(doc, schema)

        # prop1 must be either a number between 0 and 10 or 100 and 110
        schema = {'prop1':
                  {'anyof':
                   [{'min': 0, 'max': 10}, {'min': 100, 'max': 110}]}}
        doc = {'prop1': 50}

        self.assertFail(doc, schema)

        # prop1 must be an integer that is either be
        # greater than or equal to 0, or greater than or equal to 10
        schema = {'prop1': {'type': 'integer',
                            'anyof': [{'min': 0}, {'min': 10}]}}
        self.assertSuccess({'prop1': 10}, schema)
        self.assertNotIn('type', schema['prop1']['anyof'][0])
        self.assertNotIn('type', schema['prop1']['anyof'][1])
        self.assertNotIn('allow_unknown', schema['prop1']['anyof'][0])
        self.assertNotIn('allow_unknown', schema['prop1']['anyof'][1])
        self.assertSuccess({'prop1': 5}, schema)
        self.assertFail({'prop1': -1}, schema)
        exp_child_errors = [
            (('prop1',), ('prop1', 'anyof', 0, 'min'), errors.MIN_VALUE, 0),
            (('prop1',), ('prop1', 'anyof', 1, 'min'), errors.MIN_VALUE, 10)
        ]
        self.assertChildErrors(('prop1',), ('prop1', 'anyof'), errors.ANYOF,
                               [{'min': 0}, {'min': 10}],
                               child_errors=exp_child_errors)
        doc = {'prop1': 5.5}
        self.assertFail(doc, schema)
        doc = {'prop1': '5.5'}
        self.assertFail(doc, schema)

    def test_allof(self):
        # prop1 has to be a float between 0 and 10
        schema = {'prop1': {'allof': [
                 {'type': 'float'}, {'min': 0}, {'max': 10}]}}
        doc = {'prop1': -1}
        self.assertFail(doc, schema)
        doc = {'prop1': 5}
        self.assertSuccess(doc, schema)
        doc = {'prop1': 11}
        self.assertFail(doc, schema)

        # prop1 has to be a float and an integer
        schema = {'prop1': {'allof': [{'type': 'float'}, {'type': 'integer'}]}}
        doc = {'prop1': 11}
        self.assertSuccess(doc, schema)
        doc = {'prop1': 11.5}
        self.assertFail(doc, schema)
        doc = {'prop1': '11'}
        self.assertFail(doc, schema)

    def test_oneof(self):
        # prop1 can only only be:
        # - greater than 10
        # - greater than 0
        # - equal to -5, 5, or 15

        schema = {'prop1': {'type': 'integer', 'oneof': [
                 {'min': 0},
                 {'min': 10},
                 {'allowed': [-5, 5, 15]}]}}

        # document is not valid
        # prop1 not greater than 0, 10 or equal to -5
        doc = {'prop1': -1}
        self.assertFail(doc, schema)

        # document is valid
        # prop1 is less then 0, but is -5
        doc = {'prop1': -5}
        self.assertSuccess(doc, schema)

        # document is valid
        # prop1 greater than 0
        doc = {'prop1': 1}
        self.assertSuccess(doc, schema)

        # document is not valid
        # prop1 is greater than 0
        # and equal to 5
        doc = {'prop1': 5}
        self.assertFail(doc, schema)

        # document is not valid
        # prop1 is greater than 0
        # and greater than 10
        doc = {'prop1': 11}
        self.assertFail(doc, schema)

        # document is not valid
        # prop1 is greater than 0
        # and greater than 10
        # and equal to 15
        doc = {'prop1': 15}
        self.assertFail(doc, schema)

    def test_noneof(self):
        # prop1 can not be:
        # - greater than 10
        # - greater than 0
        # - equal to -5, 5, or 15

        schema = {'prop1': {'type': 'integer', 'noneof': [
                 {'min': 0},
                 {'min': 10},
                 {'allowed': [-5, 5, 15]}]}}

        # document is valid
        doc = {'prop1': -1}
        self.assertSuccess(doc, schema)

        # document is not valid
        # prop1 is equal to -5
        doc = {'prop1': -5}
        self.assertFail(doc, schema)

        # document is not valid
        # prop1 greater than 0
        doc = {'prop1': 1}
        self.assertFail(doc, schema)

        # document is not valid
        doc = {'prop1': 5}
        self.assertFail(doc, schema)

        # document is not valid
        doc = {'prop1': 11}
        self.assertFail(doc, schema)

        # document is not valid
        # and equal to 15
        doc = {'prop1': 15}
        self.assertFail(doc, schema)

    def test_anyof_allof(self):

        # prop1 can be any number outside of [0-10]
        schema = {'prop1': {'allof': [{'anyof': [{'type': 'float'},
                                                 {'type': 'integer'}]},
                                      {'anyof': [{'min': 10},
                                                 {'max': 0}]}
                                      ]}}

        doc = {'prop1': 11}
        self.assertSuccess(doc, schema)
        doc = {'prop1': -1}
        self.assertSuccess(doc, schema)
        doc = {'prop1': 5}
        self.assertFail(doc, schema)

        doc = {'prop1': 11.5}
        self.assertSuccess(doc, schema)
        doc = {'prop1': -1.5}
        self.assertSuccess(doc, schema)
        doc = {'prop1': 5.5}
        self.assertFail(doc, schema)

        doc = {'prop1': '5.5'}
        self.assertFail(doc, schema)

    def test_anyof_schema(self):
        # test that a list of schemas can be specified.

        valid_parts = [{'schema': {'model number': {'type': 'string'},
                                   'count': {'type': 'integer'}}},
                       {'schema': {'serial number': {'type': 'string'},
                                   'count': {'type': 'integer'}}}]
        valid_item = {'type': ['dict', 'string'], 'anyof': valid_parts}
        schema = {'parts': {'type': 'list', 'schema': valid_item}}
        document = {'parts': [{'model number': 'MX-009', 'count': 100},
                              {'serial number': '898-001'},
                              'misc']}

        # document is valid. each entry in 'parts' matches a type or schema
        self.assertSuccess(document, schema)

        document['parts'].append({'product name': "Monitors", 'count': 18})
        # document is invalid. 'product name' does not match any valid schemas
        self.assertFail(document, schema)

        document['parts'].pop()
        # document is valid again
        self.assertSuccess(document, schema)

        document['parts'].append({'product name': "Monitors", 'count': 18})
        document['parts'].append(10)
        # and invalid. numbers are not allowed.
        self.assertFail(document, schema)

        self.assertEqual(len(self.validator._errors), 1)
        self.assertEqual(len(self.validator._errors[0].child_errors), 2)

        exp_child_errors = [
            (('parts', 3), ('parts', 'schema', 'anyof'), errors.ANYOF,
             valid_parts),
            (('parts', 4), ('parts', 'schema', 'type'), errors.BAD_TYPE,
             ['dict', 'string'])
        ]
        self.assertChildErrors(
            'parts', ('parts', 'schema'), errors.SEQUENCE_SCHEMA, valid_item,
            child_errors=exp_child_errors
        )

        self.assertNoError(('parts', 4), ('parts', 'schema', 'anyof'),
                           errors.ANYOF, valid_parts)

        v_errors = self.validator.errors
        self.assertIn('parts', v_errors)
        self.assertIn(3, v_errors['parts'][-1])
        self.assertIn('anyof', v_errors['parts'][-1][3][-1])
        self.assertEqual(v_errors['parts'][-1][3][-1]['anyof'][0],
                         "no definitions validate")
        scope = v_errors['parts'][-1][3][-1]['anyof'][-1]
        self.assertIn('anyof definition 0', scope)
        self.assertIn('anyof definition 1', scope)
        self.assertEqual(scope['anyof definition 0'], ["unknown field"])
        self.assertEqual(scope['anyof definition 1'], ["unknown field"])
        self.assertEqual(
            v_errors['parts'][-1][4],
            ["must be of ['dict', 'string'] type"])

    def test_anyof_2(self):
        # these two schema should be the same
        schema1 = {'prop': {'anyof': [{'type': 'dict',
                                       'schema': {
                                           'val': {'type': 'integer'}}},
                                      {'type': 'dict',
                                       'schema': {
                                           'val': {'type': 'string'}}}]}}
        schema2 = {'prop': {'type': 'dict', 'anyof': [
                           {'schema': {'val': {'type': 'integer'}}},
                           {'schema': {'val': {'type': 'string'}}}]}}

        doc = {'prop': {'val': 0}}
        self.assertSuccess(doc, schema1)
        self.assertSuccess(doc, schema2)

        doc = {'prop': {'val': '0'}}
        self.assertSuccess(doc, schema1)
        self.assertSuccess(doc, schema2)

        doc = {'prop': {'val': 1.1}}
        self.assertFail(doc, schema1)
        self.assertFail(doc, schema2)

    def test_anyof_type(self):
        schema = {'anyof_type': {'anyof_type': ['string', 'integer']}}
        self.assertSuccess({'anyof_type': 'bar'}, schema)
        self.assertSuccess({'anyof_type': 23}, schema)

    def test_oneof_schema(self):
        schema = {'oneof_schema': {'type': 'dict',
                                   'oneof_schema':
                                       [{'digits': {'type': 'integer',
                                                    'min': 0, 'max': 99}},
                                        {'text': {'type': 'string',
                                                  'regex': '^[0-9]{2}$'}}]}}
        self.assertSuccess({'oneof_schema': {'digits': 19}}, schema)
        self.assertSuccess({'oneof_schema': {'text': '84'}}, schema)
        self.assertFail({'oneof_schema': {'digits': 19, 'text': '84'}}, schema)

    def test_nested_oneof_type(self):
        schema = {'nested_oneof_type':
                  {'valueschema': {'oneof_type': ['string', 'integer']}}}
        self.assertSuccess({'nested_oneof_type': {'foo': 'a'}}, schema)
        self.assertSuccess({'nested_oneof_type': {'bar': 3}}, schema)

    def test_no_of_validation_if_type_fails(self):
        valid_parts = [{'schema': {'model number': {'type': 'string'},
                                   'count': {'type': 'integer'}}},
                       {'schema': {'serial number': {'type': 'string'},
                                   'count': {'type': 'integer'}}}]
        schema = {'part': {'type': ['dict', 'string'], 'anyof': valid_parts}}
        document = {'part': 10}
        self.assertFail(document, schema)
        self.assertEqual(len(self.validator._errors), 1)

    def test_issue_107(self):
        schema = {'info': {'type': 'dict',
                  'schema': {'name': {'type': 'string', 'required': True}}}}
        document = {'info': {'name': 'my name'}}
        self.assertSuccess(document, schema)

        v = Validator(schema)
        self.assertSuccess(document, schema, v)
        # it once was observed that this behaves other than the previous line
        self.assertTrue(v.validate(document))

    def test_dont_type_validate_nulled_values(self):
        self.assertFail({'an_integer': None})
        self.assertDictEqual(self.validator.errors,
                             {'an_integer': ['null value not allowed']})

    def test_dependencies_error(self):
        v = self.validator
        schema = {'field1': {'required': False},
                  'field2': {'required': True,
                             'dependencies': {'field1': ['one', 'two']}}}
        v.validate({'field2': 7}, schema)
        exp_msg = errors.BasicErrorHandler\
            .messages[errors.DEPENDENCIES_FIELD_VALUE.code]\
            .format(field='field2', constraint={'field1': ['one', 'two']})
        self.assertDictEqual(v.errors, {'field2': [exp_msg]})

    def test_dependencies_on_boolean_field_with_one_value(self):
        # https://github.com/nicolaiarocci/cerberus/issues/138
        schema = {'deleted': {'type': 'boolean'},
                  'text': {'dependencies': {'deleted': False}}}
        try:
            self.assertSuccess({'text': 'foo', 'deleted': False}, schema)
            self.assertFail({'text': 'foo', 'deleted': True}, schema)
            self.assertFail({'text': 'foo'}, schema)
        except TypeError as e:
            if str(e) == "argument of type 'bool' is not iterable":
                self.fail(' '.join([
                    "Bug #138 still exists, couldn't use boolean",
                    "in dependency without putting it in a list.\n",
                    "'some_field': True vs 'some_field: [True]"]))
            else:
                raise

    def test_dependencies_on_boolean_field_with_value_in_list(self):
        # https://github.com/nicolaiarocci/cerberus/issues/138
        schema = {'deleted': {'type': 'boolean'},
                  'text': {'dependencies': {'deleted': [False]}}}

        self.assertSuccess({'text': 'foo', 'deleted': False}, schema)
        self.assertFail({'text': 'foo', 'deleted': True}, schema)
        self.assertFail({'text': 'foo'}, schema)

    def test_document_path(self):
        class DocumentPathTester(Validator):
            def _validate_trail(self, constraint, field, value):
                """ {'type': 'boolean'} """
                test_doc = self.root_document
                for crumb in self.document_path:
                    test_doc = test_doc[crumb]
                assert test_doc == self.document

        v = DocumentPathTester()
        schema = {'foo': {'schema': {'bar': {'trail': True}}}}
        document = {'foo': {'bar': {}}}
        self.assertSuccess(document, schema, v)

    def test_excludes(self):
        schema = {'this_field': {'type': 'dict',
                                 'excludes': 'that_field'},
                  'that_field': {'type': 'dict'}}
        document1 = {'this_field': {}}
        document2 = {'that_field': {}}
        document3 = {'that_field': {}, 'this_field': {}}
        self.assertSuccess(document1, schema)
        self.assertSuccess(document2, schema)
        self.assertSuccess({}, schema)
        self.assertFail(document3, schema)

    def test_mutual_excludes(self):
        schema = {'this_field': {'type': 'dict',
                                 'excludes': 'that_field'},
                  'that_field': {'type': 'dict',
                                 'excludes': 'this_field'}}
        document1 = {'this_field': {}}
        document2 = {'that_field': {}}
        document3 = {'that_field': {}, 'this_field': {}}
        self.assertSuccess(document1, schema)
        self.assertSuccess(document2, schema)
        self.assertSuccess({}, schema)
        self.assertFail(document3, schema)

    def test_required_excludes(self):
        schema = {'this_field': {'type': 'dict',
                                 'excludes': 'that_field',
                                 'required': True},
                  'that_field': {'type': 'dict',
                                 'excludes': 'this_field',
                                 'required': True}}
        document1 = {'this_field': {}}
        document2 = {'that_field': {}}
        document3 = {'that_field': {}, 'this_field': {}}
        self.assertSuccess(document1, schema, update=False)
        self.assertSuccess(document2, schema, update=False)
        self.assertFail({}, schema)
        self.assertFail(document3, schema)

    def test_multiples_exclusions(self):
        schema = {'this_field': {'type': 'dict',
                                 'excludes': ['that_field', 'bazo_field']},
                  'that_field': {'type': 'dict',
                                 'excludes': 'this_field'},
                  'bazo_field': {'type': 'dict'}}
        document1 = {'this_field': {}}
        document2 = {'that_field': {}}
        document3 = {'this_field': {}, 'that_field': {}}
        document4 = {'this_field': {}, 'bazo_field': {}}
        document5 = {'that_field': {}, 'this_field': {}, 'bazo_field': {}}
        document6 = {'that_field': {}, 'bazo_field': {}}
        self.assertSuccess(document1, schema)
        self.assertSuccess(document2, schema)
        self.assertFail(document3, schema)
        self.assertFail(document4, schema)
        self.assertFail(document5, schema)
        self.assertSuccess(document6, schema)

    def test_bad_excludes_fields(self):
        schema = {'this_field': {'type': 'dict',
                                 'excludes': ['that_field', 'bazo_field'],
                                 'required': True},
                  'that_field': {'type': 'dict',
                                 'excludes': 'this_field',
                                 'required': True}}
        self.assertFail({'that_field': {}, 'this_field': {}}, schema)
        handler = errors.BasicErrorHandler
        self.assertDictEqual(
            self.validator.errors,
            {'that_field':
             [handler.messages[errors.EXCLUDES_FIELD.code].format(
                 "'this_field'", field="that_field")],
             'this_field':
             [handler.messages[errors.EXCLUDES_FIELD.code].format(
                 "'that_field', 'bazo_field'", field="this_field")]})

    def test_boolean_is_not_a_number(self):
        # https://github.com/nicolaiarocci/cerberus/issues/144
        self.assertFail({'value': True}, {'value': {'type': 'number'}})

    def test_min_max_date(self):
        schema = {'date': {'min': date(1900, 1, 1), 'max': date(1999, 12, 31)}}
        self.assertSuccess({'date': date(1945, 5, 8)}, schema)
        self.assertFail({'date': date(1871, 5, 10)}, schema)

    def test_dict_length(self):
        schema = {'dict': {'minlength': 1}}
        self.assertFail({'dict': {}}, schema)
        self.assertSuccess({'dict': {'foo': 'bar'}}, schema)

    def test_forbidden(self):
        schema = {'user': {'forbidden': ['root', 'admin']}}
        self.assertFail({'user': 'admin'}, schema)
        self.assertSuccess({'user': 'alice'}, schema)

    def test_mapping_with_sequence_schema(self):
        schema = {'list': {'schema': {'allowed': ['a', 'b', 'c']}}}
        document = {'list': {'is_a': 'mapping'}}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('list', ('list', 'schema'),
                         errors.BAD_TYPE_FOR_SCHEMA, schema['list']['schema'],
                         v_errors=_errors)

    def test_sequence_with_mapping_schema(self):
        schema = {'list': {'schema': {'foo': {'allowed': ['a', 'b', 'c']}},
                           'type': 'dict'}}
        document = {'list': ['a', 'b', 'c']}
        self.assertFail(document, schema)

    def test_type_error_aborts_validation(self):
        schema = {'foo': {'type': 'string', 'allowed': ['a']}}
        document = {'foo': 0}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('foo', ('foo', 'type'), errors.BAD_TYPE, 'string',
                         v_errors=_errors)

    def test_dependencies_in_oneof(self):
        # https://github.com/nicolaiarocci/cerberus/issues/241
        schema = {'a': {'type': 'integer',
                        'oneof': [
                            {'allowed': [1], 'dependencies': 'b'},
                            {'allowed': [2], 'dependencies': 'c'}
                        ]},
                  'b': {},
                  'c': {}}
        self.assertSuccess({'a': 1, 'b': 'foo'}, schema)
        self.assertSuccess({'a': 2, 'c': 'bar'}, schema)
        self.assertFail({'a': 1, 'c': 'foo'}, schema)
        self.assertFail({'a': 2, 'b': 'bar'}, schema)

    def test_allow_unknown_with_oneof_rules(self):
        # https://github.com/nicolaiarocci/cerberus/issues/251
        schema = {
            'test': {
                'oneof': [
                    {
                        'type': 'dict',
                        'allow_unknown': True,
                        'schema': {'known': {'type': 'string'}}
                    },
                    {
                        'type': 'dict',
                        'schema': {'known': {'type': 'string'}}
                    },
                ]
            }
        }
        # check regression and that allow unknown does not cause any different
        # than expected behaviour for one-of.
        document = {'test': {'known': 's'}}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('test', ('test', 'oneof'),
                         errors.ONEOF, schema['test']['oneof'],
                         v_errors=_errors)
        self.assertEqual(len(_errors[0].child_errors), 0)
        # check that allow_unknown is actually applied
        document = {'test': {'known': 's', 'unknown': 'asd'}}
        self.assertSuccess(document, schema)


class TestNormalization(TestBase):
    def test_coerce(self):
        schema = {'amount': {'coerce': int}}
        document = {'amount': '1'}
        expected = {'amount': 1}
        self.assertNormalized(document, expected, schema)

    def test_coerce_in_subschema(self):
        schema = {'thing': {'type': 'dict',
                            'schema': {'amount': {'coerce': int}}}}
        document = {'thing': {'amount': '2'}}
        expected = {'thing': {'amount': 2}}
        self.assertNormalized(document, expected, schema)

    def test_coerce_not_destructive(self):
        schema = {
            'amount': {'coerce': int}
        }
        v = Validator(schema)
        doc = {'amount': '1'}
        v.validate(doc)
        self.assertIsNot(v.document, doc)

    def test_coerce_catches_ValueError(self):
        schema = {
            'amount': {'coerce': int}
        }
        v = Validator(schema)
        self.assertFail({'amount': 'not_a_number'}, validator=v)
        v._errors[0].info = ()
        self.assertError('amount', ('amount', 'coerce'),
                         errors.COERCION_FAILED, int, v_errors=v._errors)

    def test_coerce_catches_TypeError(self):
        schema = {
            'name': {'coerce': str.lower}
        }
        v = Validator(schema)
        self.assertFail({'name': 1234}, validator=v)
        v._errors[0].info = ()  # Volkswagen.test()
        self.assertError('name', ('name', 'coerce'), errors.COERCION_FAILED, str.lower, v_errors=v._errors)  # noqa

    def test_coerce_unknown(self):
        schema = {'foo': {'schema': {}, 'allow_unknown': {'coerce': int}}}
        document = {'foo': {'bar': '0'}}
        expected = {'foo': {'bar': 0}}
        self.assertNormalized(document, expected, schema)

    def test_normalized(self):
        schema = {'amount': {'coerce': int}}
        document = {'amount': '2'}
        expected = {'amount': 2}
        self.assertNormalized(document, expected, schema)

    def test_rename(self):
        schema = {'foo': {'rename': 'bar'}}
        document = {'foo': 0}
        expected = {'bar': 0}
        # We cannot use assertNormalized here since there is bug where
        # Cerberus says that the renamed field is an unknown field:
        # {'bar': 'unknown field'}
        self.validator(document, schema, False)
        self.assertDictEqual(self.validator.document, expected)

    def test_rename_handler(self):
        validator = Validator(allow_unknown={'rename_handler': int})
        schema = {}
        document = {'0': 'foo'}
        expected = {0: 'foo'}
        self.assertNormalized(document, expected, schema, validator)

    def test_purge_unknown(self):
        validator = Validator(purge_unknown=True)
        schema = {'foo': {'type': 'string'}}
        document = {'bar': 'foo'}
        expected = {}
        self.assertNormalized(document, expected, schema, validator)

    def test_purge_unknown_in_subschema(self):
        schema = {'foo': {'type': 'dict',
                          'schema': {'foo': {'type': 'string'}},
                          'purge_unknown': True}}
        document = {'foo': {'bar': ''}}
        expected = {'foo': {}}
        self.assertNormalized(document, expected, schema)

    def test_issue_147_complex(self):
        schema = {'revision': {'coerce': int}}
        document = {'revision': '5', 'file': NamedTemporaryFile(mode='w+')}
        document['file'].write(r'foobar')
        document['file'].seek(0)
        normalized = Validator(schema, allow_unknown=True).normalized(document)
        self.assertEqual(normalized['revision'], 5)
        self.assertEqual(normalized['file'].read(), 'foobar')
        document['file'].close()
        normalized['file'].close()

    def test_issue_147_nested_dict(self):
        schema = {'thing': {'type': 'dict',
                            'schema': {'amount': {'coerce': int}}}}
        ref_obj = '2'
        document = {'thing': {'amount': ref_obj}}
        normalized = Validator(schema).normalized(document)
        self.assertIsNot(document, normalized)
        self.assertEqual(normalized['thing']['amount'], 2)
        self.assertEqual(ref_obj, '2')
        self.assertIs(document['thing']['amount'], ref_obj)

    def test_coerce_in_valueschema(self):
        # https://github.com/nicolaiarocci/cerberus/issues/155
        schema = {'thing': {'type': 'dict',
                            'valueschema': {'coerce': int,
                                            'type': 'integer'}}}
        document = {'thing': {'amount': '2'}}
        expected = {'thing': {'amount': 2}}
        self.assertNormalized(document, expected, schema)

    def test_coerce_in_keyschema(self):
        # https://github.com/nicolaiarocci/cerberus/issues/155
        schema = {'thing': {'type': 'dict',
                            'keyschema': {'coerce': int, 'type': 'integer'}}}
        document = {'thing': {'5': 'foo'}}
        expected = {'thing': {5: 'foo'}}
        self.assertNormalized(document, expected, schema)

    def test_coercion_of_sequence_items(self):
        # https://github.com/nicolaiarocci/cerberus/issues/161
        schema = {'a_list': {'type': 'list', 'schema': {'type': 'float',
                                                        'coerce': float}}}
        document = {'a_list': [3, 4, 5]}
        expected = {'a_list': [3.0, 4.0, 5.0]}
        self.assertNormalized(document, expected, schema)
        for x in self.validator.document['a_list']:
            self.assertIsInstance(x, float)

    def test_default_missing(self):
        self._test_default_missing({'default': 'bar_value'})

    def test_default_setter_missing(self):
        self._test_default_missing({'default_setter': lambda doc: 'bar_value'})

    def _test_default_missing(self, default):
        bar_schema = {'type': 'string'}
        bar_schema.update(default)
        schema = {'foo': {'type': 'string'},
                  'bar': bar_schema}
        document = {'foo': 'foo_value'}
        expected = {'foo': 'foo_value', 'bar': 'bar_value'}
        self.assertNormalized(document, expected, schema)

    def test_default_existent(self):
        self._test_default_existent({'default': 'bar_value'})

    def test_default_setter_existent(self):
        def raise_error(doc):
            raise RuntimeError('should not be called')
        self._test_default_existent({'default_setter': raise_error})

    def _test_default_existent(self, default):
        bar_schema = {'type': 'string'}
        bar_schema.update(default)
        schema = {'foo': {'type': 'string'},
                  'bar': bar_schema}
        document = {'foo': 'foo_value', 'bar': 'non_default'}
        self.assertNormalized(document, document.copy(), schema)

    def test_default_none_nullable(self):
        self._test_default_none_nullable({'default': 'bar_value'})

    def test_default_setter_none_nullable(self):
        def raise_error(doc):
            raise RuntimeError('should not be called')
        self._test_default_none_nullable({'default_setter': raise_error})

    def _test_default_none_nullable(self, default):
        bar_schema = {'type': 'string',
                      'nullable': True}
        bar_schema.update(default)
        schema = {'foo': {'type': 'string'},
                  'bar': bar_schema}
        document = {'foo': 'foo_value', 'bar': None}
        self.assertNormalized(document, document.copy(), schema)

    def test_default_none_nonnullable(self):
        self._test_default_none_nullable({'default': 'bar_value'})

    def test_default_setter_none_nonnullable(self):
        self._test_default_none_nullable(
            {'default_setter': lambda doc: 'bar_value'})

    def _test_default_none_nonnullable(self, default):
        bar_schema = {'type': 'string',
                      'nullable': False}
        bar_schema.update(default)
        schema = {'foo': {'type': 'string'},
                  'bar': bar_schema}
        document = {'foo': 'foo_value', 'bar': 'bar_value'}
        self.assertNormalized(document, document.copy(), schema)

    def test_default_none_default_value(self):
        schema = {'foo': {'type': 'string'},
                  'bar': {'type': 'string',
                          'nullable': True,
                          'default': None}}
        document = {'foo': 'foo_value'}
        expected = {'foo': 'foo_value', 'bar': None}
        self.assertNormalized(document, expected, schema)

    def test_default_missing_in_subschema(self):
        self._test_default_missing_in_subschema({'default': 'bar_value'})

    def test_default_setter_missing_in_subschema(self):
        self._test_default_missing_in_subschema(
            {'default_setter': lambda doc: 'bar_value'})

    def _test_default_missing_in_subschema(self, default):
        bar_schema = {'type': 'string'}
        bar_schema.update(default)
        schema = {'thing': {'type': 'dict',
                            'schema': {'foo': {'type': 'string'},
                                       'bar': bar_schema}}}
        document = {'thing': {'foo': 'foo_value'}}
        expected = {'thing': {'foo': 'foo_value',
                              'bar': 'bar_value'}}
        self.assertNormalized(document, expected, schema)

    def test_depending_default_setters(self):
        schema = {
            'a': {'type': 'integer'},
            'b': {'type': 'integer', 'default_setter': lambda d: d['a'] + 1},
            'c': {'type': 'integer', 'default_setter': lambda d: d['b'] * 2},
            'd': {'type': 'integer',
                  'default_setter': lambda d: d['b'] + d['c']}
        }
        document = {'a': 1}
        expected = {'a': 1, 'b': 2, 'c': 4, 'd': 6}
        self.assertNormalized(document, expected, schema)

    def test_circular_depending_default_setters(self):
        schema = {
            'a': {'type': 'integer', 'default_setter': lambda d: d['b'] + 1},
            'b': {'type': 'integer', 'default_setter': lambda d: d['a'] + 1}
        }
        self.validator({}, schema)
        self.assertIn(errors.SETTING_DEFAULT_FAILED, self.validator._errors)

    def test_custom_coerce_and_rename(self):
        class MyNormalizer(Validator):
            def __init__(self, multiplier, *args, **kwargs):
                super(MyNormalizer, self).__init__(*args, **kwargs)
                self.multiplier = multiplier

            def _normalize_coerce_multiply(self, value):
                return value * self.multiplier

        v = MyNormalizer(2, {'foo': {'coerce': 'multiply'}})
        self.assertEqual(v.normalized({'foo': 2})['foo'], 4)

        v = MyNormalizer(3, allow_unknown={'rename_handler': 'multiply'})
        self.assertEqual(v.normalized({3: None}), {9: None})

    def test_coerce_chain(self):
        drop_prefix = lambda x: x[2:]
        upper = lambda x: x.upper()
        schema = {'foo': {'coerce': [hex, drop_prefix, upper]}}
        self.assertNormalized({'foo': 15}, {'foo': 'F'}, schema)

    def test_coerce_chain_aborts(self):
        def dont_do_me(value):
            raise AssertionError('The coercion chain did not abort after an '
                                 'error.')
        schema = {'foo': {'coerce': [hex, dont_do_me]}}
        self.validator({'foo': '0'}, schema)
        self.assertIn(errors.COERCION_FAILED, self.validator._errors)

    def test_coerce_non_digit_in_sequence(self):
        # https://github.com/nicolaiarocci/cerberus/issues/211
        schema = {'data': {'type': 'list',
                           'schema': {'type': 'integer', 'coerce': int}}}
        document = {'data': ['q']}
        self.assertEqual(self.validator.validated(document, schema),
                         None)
        self.assertEqual(
            self.validator.validated(document, schema,
                                     always_return_document=True),
            document)

    def test_issue_250(self):
        # https://github.com/nicolaiarocci/cerberus/issues/250
        schema = {
            'list': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'allow_unknown': True,
                    'schema': {'a': {'type': 'string'}}
                }
            }
        }
        document = {'list': {'is_a': 'mapping'}}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('list', ('list', 'type'),
                         errors.BAD_TYPE, schema['list']['type'],
                         v_errors=_errors)

    def test_issue_250_no_type_pass_on_list(self):
        # https://github.com/nicolaiarocci/cerberus/issues/250
        schema = {
            'list': {
                'schema': {
                    'allow_unknown': True,
                    'type': 'dict',
                    'schema': {'a': {'type': 'string'}}
                }
            }
        }
        document = {'list': [{'a': 'known', 'b': 'unknown'}]}
        self.assertNormalized(document, document, schema)

    def test_issue_250_no_type_fail_on_dict(self):
        # https://github.com/nicolaiarocci/cerberus/issues/250
        schema = {
            'list': {
                'schema': {
                    'allow_unknown': True,
                    'schema': {'a': {'type': 'string'}}
                }
            }
        }
        document = {'list': {'a': {'a': 'known'}}}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('list', ('list', 'schema'),
                         errors.BAD_TYPE_FOR_SCHEMA, schema['list']['schema'],
                         v_errors=_errors)

    def test_issue_250_no_type_fail_pass_on_other(self):
        # https://github.com/nicolaiarocci/cerberus/issues/250
        schema = {
            'list': {
                'schema': {
                    'allow_unknown': True,
                    'schema': {'a': {'type': 'string'}}
                }
            }
        }
        document = {'list': 1}
        self.assertNormalized(document, document, schema)

    def test_allow_unknown_with_of_rules(self):
        # https://github.com/nicolaiarocci/cerberus/issues/251
        schema = {
            'test': {
                'oneof': [
                    {
                        'type': 'dict',
                        'allow_unknown': True,
                        'schema': {'known': {'type': 'string'}}
                    },
                    {
                        'type': 'dict',
                        'schema': {'known': {'type': 'string'}}
                    },
                ]
            }
        }
        # check regression and that allow unknown does not cause any different
        # than expected behaviour for one-of.
        document = {'test': {'known': 's'}}
        self.validator(document, schema)
        _errors = self.validator._errors
        self.assertEqual(len(_errors), 1)
        self.assertError('test', ('test', 'oneof'),
                         errors.ONEOF, schema['test']['oneof'],
                         v_errors=_errors)
        # check that allow_unknown is actually applied
        document = {'test': {'known': 's', 'unknown': 'asd'}}


class TestDefinitionSchema(TestBase):
    def test_empty_schema(self):
        v = Validator()
        self.assertSchemaError(self.document, None, v,
                               errors.SCHEMA_ERROR_MISSING)

    def test_bad_schema_type(self):
        schema = "this string should really be dict"
        try:
            Validator(schema)
        except SchemaError as e:
            self.assertEqual(str(e),
                             errors.SCHEMA_ERROR_DEFINITION_TYPE
                             .format(schema))
        else:
            self.fail('SchemaError not raised')

        v = Validator()
        self.assertSchemaError(self.document, schema, v,
                               errors.SCHEMA_ERROR_DEFINITION_TYPE
                               .format(schema))

    def test_bad_schema_type_field(self):
        field = 'foo'
        schema = {field: {'schema': {'bar': {'type': 'strong'}}}}
        self.assertSchemaError(self.document, schema)

    def test_invalid_schema(self):
        self.assertSchemaError({}, {'foo': {'unknown': 'rule'}}, None,
                               "{'foo': [{'unknown': ['unknown rule']}]}")

    def test_unknown_rule(self):
        field = 'name'
        rule = 'unknown_rule'
        schema = {field: {rule: True, 'type': 'string'}}
        self.assertSchemaError(
            self.document, schema, None,
            str({field: [{rule: ['unknown rule']}]}))

    def test_unknown_type(self):
        field = 'name'
        value = 'catch_me'
        schema = {field: {'type': value}}
        self.assertSchemaError(
            self.document, schema, None,
            str({field: [{'type': ['unallowed value %s' % value]}]}))

    def test_bad_schema_definition(self):
        field = 'name'
        schema = {field: 'this should really be a dict'}
        self.assertSchemaError(self.document, schema, None,
                               str({field: ['must be of dict type']}))

    def bad_of_rules(self):
        schema = {'foo': {'anyof': {'type': 'string'}}}
        self.assertSchemaError({}, schema)

    def test_anyof_allof_schema_validate(self):
        # make sure schema with 'anyof' and 'allof' constraints are checked
        # correctly
        schema = {'doc': {'type': 'dict',
                          'anyof': [
                              {'schema': [{'param': {'type': 'number'}}]}]}}
        self.assertSchemaError({'doc': 'this is my document'}, schema)

        schema = {'doc': {'type': 'dict',
                          'allof': [
                              {'schema': [{'param': {'type': 'number'}}]}]}}
        self.assertSchemaError({'doc': 'this is my document'}, schema)

    def test_repr(self):
        v = Validator({'foo': {'type': 'string'}})
        self.assertEqual(repr(v.schema), "{'foo': {'type': 'string'}}")

    def test_validated_schema_cache(self):
        v = Validator({'foozifix': {'coerce': int}})
        cache_size = len(v._valid_schemas)

        v = Validator({'foozifix': {'type': 'integer'}})
        cache_size += 1
        self.assertEqual(len(v._valid_schemas), cache_size)

        v = Validator({'foozifix': {'coerce': int}})
        self.assertEqual(len(v._valid_schemas), cache_size)

        max_cache_size = 200
        self.assertLess(cache_size, max_cache_size,
                        "There's an unexpected high amount of cached valid "
                        "definition schemas. Unless you added further tests, "
                        "there are good chances that something is wrong. "
                        "If you added tests with new schemas, you can try to "
                        "adjust the variable `max_cache_size` according to "
                        "the added schemas.")

    def test_expansion_in_nested_schema(self):
        schema = {'detroit':
                  {'schema': {'anyof_regex': ['^Aladdin', 'Sane$']}}}
        v = Validator(schema)
        self.assertDictEqual(v.schema['detroit']['schema'],
                             {'anyof': [{'regex': '^Aladdin'},
                                        {'regex': 'Sane$'}]})


class TestErrorHandling(TestBase):
    def test__error_1(self):
        v = Validator(schema={'foo': {'type': 'string'}})
        v.document = {'foo': 42}
        v._error('foo', errors.BAD_TYPE, 'string')
        error = v._errors[0]
        self.assertEqual(error.document_path, ('foo',))
        self.assertEqual(error.schema_path, ('foo', 'type'))
        self.assertEqual(error.code, 0x24)
        self.assertEqual(error.rule, 'type')
        self.assertEqual(error.constraint, 'string')
        self.assertEqual(error.value, 42)
        self.assertEqual(error.info, ('string',))
        self.assertFalse(error.is_group_error)
        self.assertFalse(error.is_logic_error)

    def test__error_2(self):
        v = Validator(schema={'foo': {'keyschema': {'type': 'integer'}}})
        v.document = {'foo': {'0': 'bar'}}
        v._error('foo', errors.KEYSCHEMA, ())
        error = v._errors[0]
        self.assertEqual(error.document_path, ('foo',))
        self.assertEqual(error.schema_path, ('foo', 'keyschema'))
        self.assertEqual(error.code, 0x83)
        self.assertEqual(error.rule, 'keyschema')
        self.assertEqual(error.constraint, {'type': 'integer'})
        self.assertEqual(error.value, {'0': 'bar'})
        self.assertEqual(error.info, ((),))
        self.assertTrue(error.is_group_error)
        self.assertFalse(error.is_logic_error)

    def test__error_3(self):
        valids = [{'type': 'string', 'regex': '0x[0-9a-f]{2}'},
                  {'type': 'integer', 'min': 0, 'max': 255}]
        v = Validator(schema={'foo': {'oneof': valids}})
        v.document = {'foo': '0x100'}
        v._error('foo', errors.ONEOF, (), 0, 2)
        error = v._errors[0]
        self.assertEqual(error.document_path, ('foo',))
        self.assertEqual(error.schema_path, ('foo', 'oneof'))
        self.assertEqual(error.code, 0x92)
        self.assertEqual(error.rule, 'oneof')
        self.assertEqual(error.constraint, valids)
        self.assertEqual(error.value, '0x100')
        self.assertEqual(error.info, ((), 0, 2))
        self.assertTrue(error.is_group_error)
        self.assertTrue(error.is_logic_error)

    def test_error_tree_1(self):
        schema = {'foo': {'schema': {'bar': {'type': 'string'}}}}
        document = {'foo': {'bar': 0}}
        self.assertFail(document, schema)
        d_error_tree = self.validator.document_error_tree
        s_error_tree = self.validator.schema_error_tree
        self.assertIn('foo', d_error_tree)
        self.assertIn('bar', d_error_tree['foo'])
        self.assertEqual(d_error_tree['foo']['bar'].errors[0].value, 0)
        self.assertEqual(
            d_error_tree.fetch_errors_from(('foo', 'bar'))[0].value, 0)
        self.assertIn('foo', s_error_tree)
        self.assertIn('schema', s_error_tree['foo'])
        self.assertIn('bar', s_error_tree['foo']['schema'])
        self.assertIn('type', s_error_tree['foo']['schema']['bar'])
        self.assertEqual(
            s_error_tree['foo']['schema']['bar']['type'].errors[0].value, 0)
        self.assertEqual(
            s_error_tree.fetch_errors_from(
                ('foo', 'schema', 'bar', 'type'))[0].value, 0)

    def test_error_tree_2(self):
        schema = {'foo': {'anyof': [{'type': 'string'}, {'type': 'integer'}]}}
        document = {'foo': []}
        self.assertFail(document, schema)
        d_error_tree = self.validator.document_error_tree
        s_error_tree = self.validator.schema_error_tree
        self.assertIn('foo', d_error_tree)
        self.assertEqual(d_error_tree['foo'].errors[0].value, [])
        self.assertIn('foo', s_error_tree)
        self.assertIn('anyof', s_error_tree['foo'])
        self.assertIn(0, s_error_tree['foo']['anyof'])
        self.assertIn(1, s_error_tree['foo']['anyof'])
        self.assertIn('type', s_error_tree['foo']['anyof'][0])
        self.assertEqual(
            s_error_tree['foo']['anyof'][0]['type'].errors[0].value, [])

    def test_nested_error_paths(self):
        schema = {'a_dict': {'keyschema': {'type': 'integer'},
                             'valueschema': {'regex': '[a-z]*'}},
                  'a_list': {'schema': {'type': 'string',
                                        'oneof_regex': ['[a-z]*$', '[A-Z]*']}}}
        document = {'a_dict': {0: 'abc', 'one': 'abc', 2: 'aBc', 'three': 'abC'},  # noqa
                    'a_list': [0, 'abc', 'abC']}
        self.assertFail(document, schema)

        _det = self.validator.document_error_tree
        _set = self.validator.schema_error_tree

        self.assertEqual(len(_det.errors), 0)
        self.assertEqual(len(_set.errors), 0)

        self.assertEqual(len(_det['a_dict'].errors), 2)
        self.assertEqual(len(_set['a_dict'].errors), 0)

        self.assertIsNone(_det['a_dict'][0])
        self.assertEqual(len(_det['a_dict']['one'].errors), 1)
        self.assertEqual(len(_det['a_dict'][2].errors), 1)
        self.assertEqual(len(_det['a_dict']['three'].errors), 2)

        self.assertEqual(len(_set['a_dict']['keyschema'].errors), 1)
        self.assertEqual(len(_set['a_dict']['valueschema'].errors), 1)

        self.assertEqual(
            len(_set['a_dict']['keyschema']['type'].errors), 2)
        self.assertEqual(len(_set['a_dict']['valueschema']['regex'].errors), 2)

        _ref_err = ValidationError(
            ('a_dict', 'one'), ('a_dict', 'keyschema', 'type'),
            errors.BAD_TYPE.code, 'type', 'integer', 'one', ())
        self.assertEqual(_det['a_dict']['one'].errors[0], _ref_err)
        self.assertEqual(_set['a_dict']['keyschema']['type'].errors[0],
                         _ref_err)

        _ref_err = ValidationError(
            ('a_dict', 2), ('a_dict', 'valueschema', 'regex'),
            errors.REGEX_MISMATCH.code, 'regex', '[a-z]*$', 'aBc', ())
        self.assertEqual(_det['a_dict'][2].errors[0], _ref_err)
        self.assertEqual(
            _set['a_dict']['valueschema']['regex'].errors[0], _ref_err)

        _ref_err = ValidationError(
            ('a_dict', 'three'), ('a_dict', 'keyschema', 'type'),
            errors.BAD_TYPE.code, 'type', 'integer', 'three', ())
        self.assertEqual(_det['a_dict']['three'].errors[0], _ref_err)
        self.assertEqual(
            _set['a_dict']['keyschema']['type'].errors[1], _ref_err)

        _ref_err = ValidationError(
            ('a_dict', 'three'), ('a_dict', 'valueschema', 'regex'),
            errors.REGEX_MISMATCH.code, 'regex', '[a-z]*$', 'abC', ())
        self.assertEqual(_det['a_dict']['three'].errors[1], _ref_err)
        self.assertEqual(
            _set['a_dict']['valueschema']['regex'].errors[1], _ref_err)

        self.assertEqual(len(_det['a_list'].errors), 1)
        self.assertEqual(len(_det['a_list'][0].errors), 1)
        self.assertIsNone(_det['a_list'][1])
        self.assertEqual(len(_det['a_list'][2].errors), 3)
        self.assertEqual(len(_set['a_list'].errors), 0)
        self.assertEqual(len(_set['a_list']['schema'].errors), 1)
        self.assertEqual(len(_set['a_list']['schema']['type'].errors), 1)
        self.assertEqual(
            len(_set['a_list']['schema']['oneof'][0]['regex'].errors), 1)
        self.assertEqual(
            len(_set['a_list']['schema']['oneof'][1]['regex'].errors), 1)

        _ref_err = ValidationError(
            ('a_list', 0), ('a_list', 'schema', 'type'), errors.BAD_TYPE.code,
            'type', 'string', 0, ())
        self.assertEqual(_det['a_list'][0].errors[0], _ref_err)
        self.assertEqual(_set['a_list']['schema']['type'].errors[0], _ref_err)

        _ref_err = ValidationError(
            ('a_list', 2), ('a_list', 'schema', 'oneof'), errors.ONEOF.code,
            'oneof', 'irrelevant_at_this_point', 'abC', ())
        self.assertEqual(_det['a_list'][2].errors[0], _ref_err)
        self.assertEqual(_set['a_list']['schema']['oneof'].errors[0], _ref_err)

        _ref_err = ValidationError(
            ('a_list', 2), ('a_list', 'schema', 'oneof', 0, 'regex'),
            errors.REGEX_MISMATCH.code, 'regex', '[a-z]*$', 'abC', ())
        self.assertEqual(_det['a_list'][2].errors[1], _ref_err)
        self.assertEqual(
            _set['a_list']['schema']['oneof'][0]['regex'].errors[0], _ref_err)

        _ref_err = ValidationError(
            ('a_list', 2), ('a_list', 'schema', 'oneof', 1, 'regex'),
            errors.REGEX_MISMATCH.code, 'regex', '[a-z]*$', 'abC', ())
        self.assertEqual(_det['a_list'][2].errors[2], _ref_err)
        self.assertEqual(
            _set['a_list']['schema']['oneof'][1]['regex'].errors[0], _ref_err)

    def test_basic_error_handler(self):
        handler = errors.BasicErrorHandler()
        _errors, ref = [], {}

        _errors.append(ValidationError(
            ['foo'], ['foo'], 0x63, 'readonly', True, None, ()))
        ref.update({'foo': [handler.messages[0x63]]})
        self.assertDictEqual(handler(_errors), ref)

        _errors.append(ValidationError(
            ['bar'], ['foo'], 0x42, 'min', 1, 2, ()))
        ref.update({'bar': [handler.messages[0x42].format(constraint=1)]})
        self.assertDictEqual(handler(_errors), ref)

        _errors.append(ValidationError(
            ['zap', 'foo'], ['zap', 'schema', 'foo'], 0x24, 'type', 'string',
            True, ()))
        ref.update({'zap': [{'foo': [handler.messages[0x24].format(
            constraint='string')]}]})
        self.assertDictEqual(handler(_errors), ref)

        _errors.append(ValidationError(
            ['zap', 'foo'], ['zap', 'schema', 'foo'], 0x41, 'regex',
            '^p[äe]ng$', 'boom', ()))
        ref['zap'][0]['foo'].append(
            handler.messages[0x41].format(constraint='^p[äe]ng$'))
        self.assertDictEqual(handler(_errors), ref)

    def test_basic_error_of_errors(self):
        schema = {'foo': {'oneof': [
            {'type': 'integer'},
            {'type': 'string'}
        ]}}
        validator = Validator(schema)
        document = {'foo': 23.42}
        self.assertFalse(validator(document))
        error = ('foo', ('foo', 'oneof'), errors.ONEOF,
                 schema['foo']['oneof'], ())
        child_errors = [
            (error[0], error[1] + (0, 'type'), errors.BAD_TYPE, 'integer'),
            (error[0], error[1] + (1, 'type'), errors.BAD_TYPE, 'string')
        ]
        self.assertChildErrors(*error, child_errors=child_errors,
                               v_errors=validator._errors)
        self.assertDictEqual(validator.errors, {'foo': [{'oneof': [
            errors.BasicErrorHandler.messages[0x92],
            {'oneof definition 0': ['must be of integer type'],
             'oneof definition 1': ['must be of string type']}
        ]}]})


class TestBackwardCompatibility(TestBase):
    pass


class TestInheritance(TestBase):
    def test_contextual_data_preservation(self):

        class InheritedValidator(Validator):
            def __init__(self, *args, **kwargs):
                if 'working_dir' in kwargs:
                    self.working_dir = kwargs['working_dir']
                super(InheritedValidator, self).__init__(*args, **kwargs)

            def _validate_type_test(self, value):
                if self.working_dir:
                    return True

        self.assertIn('test', InheritedValidator.types)
        v = InheritedValidator({'test': {'type': 'list',
                                         'schema': {'type': 'test'}}},
                               working_dir='/tmp')
        self.assertSuccess({'test': ['foo']}, validator=v)

    def test_docstring_parsing(self):
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

        self.assertIn('foo', CustomValidator.validation_rules)
        self.assertIn('bar', CustomValidator.validation_rules)


class TestRegistries(TestBase):
    def test_schema_registry_simple(self):
        schema_registry.add('foo', {'bar': {'type': 'string'}})
        schema = {'a': {'schema': 'foo'},
                  'b': {'schema': 'foo'}}
        document = {'a': {'bar': 'a'}, 'b': {'bar': 'b'}}
        self.assertSuccess(document, schema)

    def test_top_level_reference(self):
        schema_registry.add('peng', {'foo': {'type': 'integer'}})
        document = {'foo': 42}
        self.assertSuccess(document, 'peng')

    def test_rules_set_simple(self):
        rules_set_registry.add('foo', {'type': 'integer'})
        self.assertSuccess({'bar': 1}, {'bar': 'foo'})
        self.assertFail({'bar': 'one'}, {'bar': 'foo'})

    def test_allow_unknown_as_reference(self):
        rules_set_registry.add('foo', {'type': 'number'})
        v = Validator(allow_unknown='foo')
        self.assertSuccess({0: 1}, {}, v)
        self.assertFail({0: 'one'}, {}, v)

    def test_recursion(self):
        rules_set_registry.add('self',
                               {'type': 'dict', 'allow_unknown': 'self'})
        v = Validator(allow_unknown='self')
        self.assertSuccess({0: {1: {2: {}}}}, {}, v)

    def test_references_remain_unresolved(self):
        rules_set_registry.extend((('boolean', {'type': 'boolean'}),
                                   ('booleans', {'valueschema': 'boolean'})))
        schema = {'foo': 'booleans'}
        self.validator.schema = schema
        self.assertEqual('booleans', self.validator.schema['foo'])
        self.assertEqual(
            'boolean', rules_set_registry._storage['booleans']['valueschema'])


class TestAssorted(TestBase):
    def test_clear_cache(self):
        self.assertGreater(len(self.validator._valid_schemas), 0)
        self.validator.clear_caches()
        self.assertEqual(len(self.validator._valid_schemas), 0)

    def test_docstring(self):
        self.assertTrue(Validator.__doc__)


if __name__ == '__main__':
    # TODO get pytest.main() working before tackling
    # https://github.com/nicolaiarocci/cerberus/issues/213
    unittest.main()
