from cerberus import errors
from cerberus.tests import assert_fail, assert_success


def test_valuesrules_succeds():
    assert_success(
        document={'a_dict_with_valuesrules': {'an integer': 99, 'another integer': 100}}
    )


def test_valuesrules_fails(validator):
    assert_fail(
        document={'a_dict_with_valuesrules': {'a string': '99'}},
        validator=validator,
        error=(
            'a_dict_with_valuesrules',
            ('a_dict_with_valuesrules', 'valuesrules'),
            errors.VALUESRULES,
            {'type': ('integer',)},
        ),
        child_errors=[
            (
                ('a_dict_with_valuesrules', 'a string'),
                ('a_dict_with_valuesrules', 'valuesrules', 'type'),
                errors.TYPE,
                ('integer',),
            )
        ],
    )

    assert 'valuesrules' in validator.schema_error_tree['a_dict_with_valuesrules']
    error_node = validator.schema_error_tree['a_dict_with_valuesrules']['valuesrules']
    assert len(error_node.descendants) == 1
