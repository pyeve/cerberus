import re
from datetime import datetime, date
from random import choice
from string import ascii_lowercase

from cerberus import errors, Validator
from cerberus.tests import TestBase


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
        assert self.validator.errors == {field: ['unknown field']}

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
        assert 'read-only' in v.errors['a_readonly_number'][0]

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
        assert field in v.errors
        assert schema_field in v.errors[field][-1]
        assert handler.messages[errors.BAD_TYPE.code] \
            .format(constraint='string') in \
            v.errors[field][-1][schema_field]
        assert 'city' in v.errors[field][-1]
        assert handler.messages[errors.REQUIRED_FIELD.code] in \
            v.errors[field][-1]['city']

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
        assert errors.BasicErrorHandler.messages[errors.BAD_TYPE.code]. \
            format(constraint='integer') in \
            self.validator.errors[field][-1][1]

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
        assert field in v.errors
        assert 0 in v.errors[field][-1]
        assert 'price' in v.errors[field][-1][0][-1]
        exp_msg = errors.BasicErrorHandler.messages[errors.BAD_TYPE.code]\
            .format(constraint='integer')
        assert exp_msg in v.errors[field][-1][0][-1]['price']

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
        assert self.validator.errors == \
            {field: [{1: ['must be of string type']}]}

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
        assert 'valueschema' in \
            self.validator.schema_error_tree['a_dict_with_valueschema']
        v = self.validator.schema_error_tree
        assert len(v['a_dict_with_valueschema']['valueschema'].descendants) == 1

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
        assert v.errors == {'test_field': ['Below the min']}

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
        assert v.errors == {'test_field': ['Not an odd number']}

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
        assert self.validator.errors == {}

    def test_callable_validator(self):
        """
        Validator instance is callable, functions as a shorthand
        passthrough to validate()
        """
        schema = {'test_field': {'type': 'string'}}
        v = Validator(schema)
        assert v.validate({'test_field': 'foo'})
        assert v({'test_field': 'foo'})
        assert not v.validate({'test_field': 1})
        assert not v({'test_field': 1})

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
        assert v.errors == {'name': ['must be lowercase']}
        self.assertSuccess({'name': 'itsme', 'age': 2}, validator=v)

    def test_validated(self):
        schema = {'property': {'type': 'string'}}
        v = Validator(schema)
        document = {'property': 'string'}
        assert v.validated(document) == document
        document = {'property': 0}
        assert v.validated(document) is None

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
        assert 'type' not in schema['prop1']['anyof'][0]
        assert 'type' not in schema['prop1']['anyof'][1]
        assert 'allow_unknown' not in schema['prop1']['anyof'][0]
        assert 'allow_unknown' not in schema['prop1']['anyof'][1]
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

        assert len(self.validator._errors) == 1
        assert len(self.validator._errors[0].child_errors) == 2

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
        assert 'parts' in v_errors
        assert 3 in v_errors['parts'][-1]
        assert 'anyof' in v_errors['parts'][-1][3][-1]
        assert v_errors['parts'][-1][3][-1]['anyof'][0] == \
            "no definitions validate"
        scope = v_errors['parts'][-1][3][-1]['anyof'][-1]
        assert 'anyof definition 0' in scope
        assert 'anyof definition 1' in scope
        assert scope['anyof definition 0'] == ["unknown field"]
        assert scope['anyof definition 1'] == ["unknown field"]
        assert v_errors['parts'][-1][4] == \
            ["must be of ['dict', 'string'] type"]

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
        assert len(self.validator._errors) == 1

    def test_issue_107(self):
        schema = {'info': {'type': 'dict',
                  'schema': {'name': {'type': 'string', 'required': True}}}}
        document = {'info': {'name': 'my name'}}
        self.assertSuccess(document, schema)

        v = Validator(schema)
        self.assertSuccess(document, schema, v)
        # it once was observed that this behaves other than the previous line
        assert v.validate(document)

    def test_dont_type_validate_nulled_values(self):
        self.assertFail({'an_integer': None})
        assert self.validator.errors == \
            {'an_integer': ['null value not allowed']}

    def test_dependencies_error(self):
        v = self.validator
        schema = {'field1': {'required': False},
                  'field2': {'required': True,
                             'dependencies': {'field1': ['one', 'two']}}}
        v.validate({'field2': 7}, schema)
        exp_msg = errors.BasicErrorHandler\
            .messages[errors.DEPENDENCIES_FIELD_VALUE.code]\
            .format(field='field2', constraint={'field1': ['one', 'two']})
        assert v.errors == {'field2': [exp_msg]}

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
        assert self.validator.errors == \
            {'that_field':
             [handler.messages[errors.EXCLUDES_FIELD.code].format(
                 "'this_field'", field="that_field")],
             'this_field':
             [handler.messages[errors.EXCLUDES_FIELD.code].format(
                 "'that_field', 'bazo_field'", field="this_field")]}

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
        assert len(_errors) == 1
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
        assert len(_errors) == 1
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
        assert len(_errors) == 1
        self.assertError('test', ('test', 'oneof'),
                         errors.ONEOF, schema['test']['oneof'],
                         v_errors=_errors)
        assert len(_errors[0].child_errors) == 0
        # check that allow_unknown is actually applied
        document = {'test': {'known': 's', 'unknown': 'asd'}}
        self.assertSuccess(document, schema)
