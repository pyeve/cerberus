from cerberus import errors
from cerberus.tests import assert_fail


def test_itemsrules():
    assert_fail(document={'a_list_of_integers': [34, 'not an integer']})


def test_itemsrules_with_schema(validator):
    field = 'a_list_of_dicts'
    mapping_schema = {
        'sku': {'type': ('string',)},
        'price': {'type': ('integer',), 'required': True},
    }
    itemsrules = {'type': ('dict',), 'schema': mapping_schema}

    assert_fail(
        schema={field: {'type': 'list', 'itemsrules': itemsrules}},
        document={field: [{'sku': 'KT123', 'price': '100'}]},
        validator=validator,
        error=(field, (field, 'itemsrules'), errors.ITEMSRULES, itemsrules),
        child_errors=[
            ((field, 0), (field, 'itemsrules', 'schema'), errors.SCHEMA, mapping_schema)
        ],
    )

    assert field in validator.errors
    assert 0 in validator.errors[field][-1]
    assert 'price' in validator.errors[field][-1][0][-1]
    exp_msg = errors.BasicErrorHandler.messages[errors.TYPE.code].format(
        constraint=('integer',)
    )
    assert exp_msg in validator.errors[field][-1][0][-1]['price']

    #

    assert_fail(
        document={field: ["not a dict"]},
        error=(field, (field, 'itemsrules'), errors.ITEMSRULES, itemsrules),
        child_errors=[
            ((field, 0), (field, 'itemsrules', 'type'), errors.TYPE, ('dict',), ())
        ],
    )
