# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import os
    import sys
    import unittest  # TODO pytest
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..', '..')))

from cerberus import errors  # noqa
from cerberus.tests import TestBase  # noqa


ValidationError = errors.ValidationError


class TestRuleFilter(TestBase):

    def test_process_no_validation_rules(self):
        self.validator.rule_filter = lambda f: False
        document = {
            'a_string': 'a',  # too short
            'a_binary': None,  # not nullable
            'an_integer': 200,  # too big
            'a_boolean': 'foo',  # wrong type
            'a_regex_email': '@',  # wrong pattern
            'a_readonly_string': 'bar',  # readonly
            'a_restricted_string': 'baz',  # forbidden value
            'an_array': ['foo', 'bar'],  # forbidden values
            'a_list_of_dicts': [
                {}, {'sku': '123'}  # missing required field price
            ],
            'a_dict_with_valueschema': {
                'foo': '1',  # not of type 'integer'
                'bar': '2',  # not of type 'integer'
            },
            'a_dict_with_keyschema': {
                '1': 'foo',  # key does not match keyschema
                '2': 'bar',  # key does not match keyschema
            }
        }
        self.assertSuccess(document)

    def test_disable_coerce(self):
        self.validator.rule_filter = lambda f: f != 'coerce'
        self.schema['an_integer']['coerce'] = lambda v: int(v)
        # The `type` rule will still be processed and let the validation fail
        self.assertFail({'an_integer': '7'})
        self.assertError('an_integer', ('an_integer', 'type'),
                         errors.BAD_TYPE, 'integer')
        self.assertEqual(self.validator.document['an_integer'], '7')

    def test_disable_default(self):
        self.validator.rule_filter = \
            lambda f: f not in ('default', 'default_setter')
        self.schema['a_string']['default'] = 'default'
        self.schema['a_number']['default_setter'] = lambda d: 2
        self.assertSuccess({})
        self.assertNotIn('a_string', self.validator.document)
        self.assertNotIn('a_number', self.validator.document)

    def test_disable_rename(self):
        self.validator.rule_filter = \
            lambda f: f not in ('rename', 'rename_handler')
        self.schema['a_string']['rename'] = 'new_string'
        self.schema['a_dict']['allow_unknown'] = {'rename_handler': int}
        document = {
            'a_string': 'foo',
            'a_dict': {'city': 'test', '2': 'foo'}
        }
        self.assertSuccess(document)
        self.assertIn('a_string', self.validator.document)
        self.assertIn('2', self.validator.document['a_dict'])

    def test_still_disallow_unknown_keys(self):
        self.validator.rule_filter = lambda f: False
        self.assertFail({'unknown': 'unknown'})
        self.assertError('unknown', (), errors.UNKNOWN_FIELD, None)

    def test_still_purge_unknown_keys(self):
        self.validator.rule_filter = lambda f: False
        self.validator.purge_unknown = True
        self.assertSuccess({'unknown': 'unknown'})
        self.assertNotIn('unknown', self.validator.document)

    def test_recurse_schema(self):
        """ We expect to validate all subdocuments even if `rule_filter`
        returns False for 'schema'. """
        self.validator.rule_filter = lambda f: f == 'required'
        self.assertSuccess({'a_list_of_dicts': []})
        self.assertFail({'a_list_of_dicts': [{}]})
        self.assertError('a_list_of_dicts', ('a_list_of_dicts', 'schema'),
                         errors.SEQUENCE_SCHEMA,
                         self.schema['a_list_of_dicts']['schema'])

    def test_recurse_schema_without_failing(self):
        self.validator.rule_filter = lambda f: f == 'readonly'
        self.assertSuccess({'a_dict': 'wrong type'})

    def test_recurse_items(self):
        """ We expect to validate all subdocuments (here: items of a list)
        even if `rule_filter` returns False for 'items'. """
        self.validator.rule_filter = lambda f: f == 'type'
        self.assertFail({'a_list_of_values': [1, 2]})
        self.assertError('a_list_of_values', ('a_list_of_values', 'items'),
                         errors.BAD_ITEMS, [{'type': 'string'},
                                            {'type': 'integer'}])

    def test_recurse_items_without_failing(self):
        """ Processing `items` would result in failure because the list
        contains the wrong number of items. But because we don't process
        `items` we don't expect the validation to fail. """
        self.validator.rule_filter = lambda f: f == 'readonly'
        self.assertSuccess({'a_list_of_values': 'wrong type'})

    def test_recurse_keyschema(self):
        self.validator.rule_filter = lambda f: f in ('type', 'regex')
        self.assertFail({'a_dict_with_keyschema': {'AAA': 1}})
        self.assertError('a_dict_with_keyschema',
                         ('a_dict_with_keyschema', 'keyschema'),
                         errors.KEYSCHEMA,
                         self.schema['a_dict_with_keyschema']['keyschema'])

    def test_recurse_keyschema_without_failing(self):
        self.validator.rule_filter = lambda f: f == 'readonly'
        self.assertSuccess({'a_dict_with_keyschema': 'wrong type'})

    def test_recurse_valueschema(self):
        self.validator.rule_filter = lambda f: f == 'type'
        self.assertFail({'a_dict_with_valueschema': {'foo': 'bar'}})
        self.assertError('a_dict_with_valueschema',
                         ('a_dict_with_valueschema', 'valueschema'),
                         errors.VALUESCHEMA,
                         self.schema['a_dict_with_valueschema']['valueschema'])

    def test_recurse_valueschema_without_failing(self):
        self.validator.rule_filter = lambda f: f == 'readonly'
        self.assertSuccess({'a_dict_with_valueschema': 'wrong type'})


if __name__ == '__main__':
    # TODO get pytest.main() working before tackling
    # https://github.com/nicolaiarocci/cerberus/issues/213
    unittest.main()
