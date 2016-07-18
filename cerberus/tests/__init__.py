from cerberus import Validator, SchemaError, DocumentError, errors

import sys
if sys.version_info >= (2, 7):
    import unittest  # noqa
else:
    import unittest2 as unittest  # noqa


class TestBase(unittest.TestCase):

    required_string_extension = {
        'a_required_string': {'type': 'string',
                              'minlength': 2,
                              'maxlength': 10,
                              'required': True}}

    def setUp(self):
        self.document = {'name': 'john doe'}
        self.schema = {
            'a_string': {
                'type': 'string',
                'minlength': 2,
                'maxlength': 10
            },
            'a_binary': {
                'type': 'binary',
                'minlength': 2,
                'maxlength': 10
            },
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
            'a_list_of_dicts': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'sku': {'type': 'string'},
                        'price': {'type': 'integer', 'required': True},
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
            'a_dict_with_keyschema': {
                'type': 'dict',
                'keyschema': {'type': 'string', 'regex': '[a-z]+'}
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
        """ Tests whether a validation raises an exception due to a malformed
            schema. """
        self.assertException(SchemaError, document, schema, validator, msg)

    def assertValidationError(self, document, schema=None, validator=None,
                              msg=None):
        """ Tests whether a validation raises an exception due to a malformed
            document. """
        self.assertException(DocumentError, document, schema, validator, msg)

    def assertException(self, known_exception, document, schema=None,
                        validator=None, msg=None):
        """ Tests whether a specific exception is raised. Optionally also tests
            if the exception message is as expected. """
        if validator is None:
            validator = self.validator
        try:
            validator(document, schema)
        except known_exception as e:
            if msg is not None:
                self.assertEqual(str(e), msg)
        except Exception as e:  # noqa
            self.fail("'%s' raised, expected %s." % (e, known_exception))
        else:
            self.fail('no exception was raised.')

    def assertFail(self, document, schema=None, validator=None, update=False):
        """ Tests whether a validation fails. """
        if validator is None:
            validator = self.validator
        self.assertFalse(validator(document, schema, update))

    def assertSuccess(self, document, schema=None, validator=None,
                      update=False):
        """ Tests whether a validation succeeds. """
        if validator is None:
            validator = self.validator
        self.assertTrue(validator(document, schema, update),
                        validator.errors)

    def assertError(self, d_path, s_path, error, constraint, info=(),
                    v_errors=None):
        if v_errors is None:
            v_errors = self.validator._errors
        assert isinstance(v_errors, list)
        if not isinstance(d_path, tuple):
            d_path = (d_path, )
        if not isinstance(info, tuple):
            info = (info, )

        in_v_errors = False
        for i, v_error in enumerate(v_errors):
            assert isinstance(v_error, errors.ValidationError)
            try:
                self.assertEqual(v_error.document_path, d_path)
                self.assertEqual(v_error.schema_path, s_path)
                self.assertEqual(v_error.code, error.code)
                self.assertEqual(v_error.rule, error.rule)
                self.assertEqual(v_error.constraint, constraint)
                if not v_error.is_group_error:
                    self.assertEqual(v_error.info, info)
            except AssertionError:
                pass
            except Exception as e:
                raise e
            else:
                in_v_errors = True
                index = i
                break
        if not in_v_errors:
            raise AssertionError("""
            Error with properties:
              document_path={doc_path}
              schema_path={schema_path}
              code={code}
              constraint={constraint}
              info={info}
            not found in errors:
            {errors}
            """.format(doc_path=d_path, schema_path=s_path,
                       code=hex(error.code), info=info,
                       constraint=constraint, errors=v_errors))

        return index

    def assertErrors(self, _errors, v_errors=None):
        assert isinstance(_errors, list)
        for error in _errors:
            assert isinstance(error, tuple)
            self.assertError(*error, v_errors=v_errors)

    def assertNoError(self, *args, **kwargs):
        try:
            self.assertError(*args, **kwargs)
        except AssertionError:
            pass
        except Exception as e:
            raise e
        else:
            raise AssertionError('An unexpected error occurred.')

    def assertChildErrors(self, *args, **kwargs):
        v_errors = kwargs.get('v_errors', self.validator._errors)
        child_errors = kwargs.get('child_errors', [])
        assert isinstance(child_errors, list)

        parent = self.assertError(*args, v_errors=v_errors)

        _errors = v_errors[parent].child_errors
        self.assertErrors(child_errors, v_errors=_errors)

    def assertBadType(self, field, data_type, value):
        self.assertFail({field: value})
        self.assertError(field, (field, 'type'), errors.BAD_TYPE, data_type)

    def assertNormalized(self, document, expected, schema=None, validator=None):
        if validator is None:
            validator = self.validator

        self.assertSuccess(document, schema, validator)
        self.assertDictEqual(validator.document, expected)
