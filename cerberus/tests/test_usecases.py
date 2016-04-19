from unittest import TestCase

from cerberus import Validator


class TestComplexCases(TestCase):
    def test_nested_list_choice_dicts(self):
        test_schema = {
            'temp': {
                'type': 'list',
                'anyof': [
                    {
                        'schema': {
                            'type': {
                                'type': 'string',
                                'required': True,
                                'nullable': False,
                                'allowed': ['tmp1'],
                            },
                            'args': {
                                'type': 'list',
                                'schema': {
                                    'type': 'string'
                                }
                            }
                        },
                    },
                ]
            }
        }
        validator = Validator(schema=test_schema)
        validator.validate(
            {
                'temp': [
                    {
                        'type': 'tmp1',
                        'args': [
                            'arg1',
                            'arg2'
                        ]
                    },
                ],
            }
        )
