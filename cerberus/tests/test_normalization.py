from tempfile import NamedTemporaryFile

from cerberus import Validator, errors
from cerberus.tests import TestBase


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
        assert v.document is not doc

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
        assert self.validator.document == expected

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
        assert normalized['revision'] == 5
        assert normalized['file'].read() == 'foobar'
        document['file'].close()
        normalized['file'].close()

    def test_issue_147_nested_dict(self):
        schema = {'thing': {'type': 'dict',
                            'schema': {'amount': {'coerce': int}}}}
        ref_obj = '2'
        document = {'thing': {'amount': ref_obj}}
        normalized = Validator(schema).normalized(document)
        assert document is not normalized
        assert normalized['thing']['amount'] == 2
        assert ref_obj == '2'
        assert document['thing']['amount'] is ref_obj

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
            assert isinstance(x, float)

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
        assert errors.SETTING_DEFAULT_FAILED in self.validator._errors

    def test_custom_coerce_and_rename(self):
        class MyNormalizer(Validator):
            def __init__(self, multiplier, *args, **kwargs):
                super(MyNormalizer, self).__init__(*args, **kwargs)
                self.multiplier = multiplier

            def _normalize_coerce_multiply(self, value):
                return value * self.multiplier

        v = MyNormalizer(2, {'foo': {'coerce': 'multiply'}})
        assert v.normalized({'foo': 2})['foo'] == 4

        v = MyNormalizer(3, allow_unknown={'rename_handler': 'multiply'})
        assert v.normalized({3: None}) == {9: None}

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
        assert errors.COERCION_FAILED in self.validator._errors

    def test_coerce_non_digit_in_sequence(self):
        # https://github.com/nicolaiarocci/cerberus/issues/211
        schema = {'data': {'type': 'list',
                           'schema': {'type': 'integer', 'coerce': int}}}
        document = {'data': ['q']}
        assert self.validator.validated(document, schema) is None
        assert self.validator.validated(document, schema,
                                        always_return_document=True) == \
            document

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
        assert len(_errors) == 1
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
        assert len(_errors) == 1
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
        assert len(_errors) == 1
        self.assertError('test', ('test', 'oneof'),
                         errors.ONEOF, schema['test']['oneof'],
                         v_errors=_errors)
        # check that allow_unknown is actually applied
        document = {'test': {'known': 's', 'unknown': 'asd'}}
