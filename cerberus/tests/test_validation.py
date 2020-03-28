import itertools
from datetime import datetime

from pytest import mark

from cerberus import errors, Validator
from cerberus.tests import (
    assert_document_error,
    assert_fail,
    assert_has_error,
    assert_not_has_error,
    assert_success,
)
from cerberus.tests.conftest import sample_schema


def test_empty_document():
    assert_document_error(None, sample_schema, None, errors.DOCUMENT_MISSING)


def test_bad_document_type():
    document = "not a dict"
    assert_document_error(
        document, sample_schema, None, errors.DOCUMENT_FORMAT.format(document)
    )


def test_unknown_field(validator):
    field = 'surname'
    assert_fail(
        {field: 'doe'},
        validator=validator,
        error=(field, (), errors.UNKNOWN_FIELD, None),
    )
    assert validator.errors == {field: ['unknown field']}


def test_empty_field_definition(document):
    field = 'name'
    schema = {field: {}}
    assert_success(document, schema)


def test_bad_valuesrules():
    field = 'a_dict_with_valuesrules'
    schema_field = 'a_string'
    value = {schema_field: 'not an integer'}

    exp_child_errors = [
        (
            (field, schema_field),
            (field, 'valuesrules', 'type'),
            errors.TYPE,
            ('integer',),
        )
    ]
    assert_fail(
        {field: value},
        error=(
            field,
            (field, 'valuesrules'),
            errors.VALUESRULES,
            {'type': ('integer',)},
        ),
        child_errors=exp_child_errors,
    )


def test_validate_update():
    assert_success(
        {
            'an_integer': 100,
            'a_dict': {'address': 'adr'},
            'a_list_of_dicts': [{'sku': 'let'}],
        },
        update=True,
    )


@mark.parametrize(
    "document",
    [
        {'a_boolean': True},
        {'a_datetime': datetime.now()},
        {'a_float': 3.5},
        {
            'a_list_of_dicts': [
                {'sku': 'AK345', 'price': 100},
                {'sku': 'YZ069', 'price': 25},
            ]
        },
        {'a_list_of_integers': [99, 100]},
        {'a_list_of_values': ['hello', 100]},
        {'a_number': 3},
        {'a_number': 3.5},
        {'a_restricted_string': 'client'},
        {'a_string': 'john doe'},
        {'an_array': ['agent', 'client']},
        {'an_integer': 50},
    ],
)
def test_success_with_multiple_rules(document):
    assert_success(document)


def test_one_of_two_types(validator):
    field = 'one_or_more_strings'
    assert_success({field: 'foo'})
    assert_success({field: ['foo', 'bar']})
    exp_child_errors = [
        ((field, 1), (field, 'itemsrules', 'type'), errors.TYPE, ('string',))
    ]
    assert_fail(
        {field: ['foo', 23]},
        validator=validator,
        error=(field, (field, 'itemsrules'), errors.ITEMSRULES, {'type': ('string',)}),
        child_errors=exp_child_errors,
    )
    assert_fail(
        {field: 23}, error=((field,), (field, 'type'), errors.TYPE, ('string', 'list'))
    )
    assert validator.errors == {
        field: [{1: ["must be one of these types: ('string',)"]}]
    }


def test_custom_validator():
    class MyValidator(Validator):
        def _validate_isodd(self, isodd, field, value):
            """ {'type': 'boolean'} """
            if isodd and not bool(value & 1):
                self._error(field, 'Not an odd number')

    schema = {'test_field': {'isodd': True}}
    validator = MyValidator(schema)
    assert_success({'test_field': 7}, validator=validator)
    assert_fail(
        {'test_field': 6},
        validator=validator,
        error=('test_field', (), errors.CUSTOM, None, ('Not an odd number',)),
    )
    assert validator.errors == {'test_field': ['Not an odd number']}


def test_ignore_none_values():
    # original commits:
    # 96532fc8efbc0b057dd6cd23d0324c8c5a929456
    # d6422991c41587467673716cb6e4e929fa9d7b77

    field = 'test'
    schema = {field: {'type': ('string',), 'empty': False, 'required': False}}
    document = {field: None}

    # Test normal behaviour
    validator = Validator(schema, ignore_none_values=False)
    assert_fail(document, validator=validator)

    validator.schema[field]['required'] = True
    validator.schema.validate()
    _errors = assert_fail(document, validator=validator)
    assert_not_has_error(
        _errors, field, (field, 'required'), errors.REQUIRED_FIELD, True
    )

    # Test ignore None behaviour
    validator = Validator(schema, ignore_none_values=True)
    validator.schema[field]['required'] = False
    validator.schema.validate()
    assert_success(document, validator=validator)

    validator.schema[field]['required'] = True
    assert validator.schema[field].get('required') is True
    _errors = assert_fail(document=document, validator=validator)
    assert_has_error(_errors, field, (field, 'required'), errors.REQUIRED_FIELD, True)
    assert_not_has_error(_errors, field, (field, 'type'), errors.TYPE, 'string')


def test_unknown_keys():
    schema = {}

    # test that unknown fields are allowed when allow_unknown is True.
    v = Validator(allow_unknown=True, schema=schema)
    assert_success({"unknown1": True, "unknown2": "yes"}, validator=v)

    # test that unknown fields are allowed only if they meet the
    # allow_unknown schema when provided.
    v.allow_unknown = {'type': 'string'}
    assert_success(document={'name': 'mark'}, validator=v)
    assert_fail({"name": 1}, validator=v)

    # test that unknown fields are not allowed if allow_unknown is False
    v.allow_unknown = False
    assert_fail({'name': 'mark'}, validator=v)


def test_unknown_key_dict(validator):
    # https://github.com/pyeve/cerberus/issues/177
    validator.allow_unknown = True
    document = {'a_dict': {'foo': 'foo_value', 'bar': 25}}
    assert_success(document, {}, validator=validator)


def test_unknown_key_list(validator):
    # https://github.com/pyeve/cerberus/issues/177
    validator.allow_unknown = True
    document = {'a_dict': ['foo', 'bar']}
    assert_success(document, {}, validator=validator)


def test_unknown_keys_list_of_dicts(validator):
    # test that allow_unknown is honored even for subdicts in lists.
    # https://github.com/pyeve/cerberus/issues/67.
    validator.allow_unknown = True
    document = {'a_list_of_dicts': [{'sku': 'YZ069', 'price': 25, 'extra': True}]}
    assert_success(document, validator=validator)


def test_unknown_keys_retain_custom_rules():
    # test that allow_unknown schema respect custom validation rules.
    # https://github.com/pyeve/cerberus/issues/#66.
    class CustomValidator(Validator):
        def _check_with_foo(self, field, value):
            return value == "foo"

    validator = CustomValidator({})
    validator.allow_unknown = {"check_with": "foo"}
    assert_success(document={"fred": "foo", "barney": "foo"}, validator=validator)


def test_callable_validator():
    """
    Validator instance is callable, functions as a shorthand
    passthrough to validate()
    """
    schema = {'test_field': {'type': 'string'}}
    validator = Validator(schema)
    assert validator.validate({'test_field': 'foo'})
    assert validator({'test_field': 'foo'})
    assert not validator.validate({'test_field': 1})
    assert not validator({'test_field': 1})


def test_self_root_document():
    """ Make sure self.root_document is always the root document.
    See:
    * https://github.com/pyeve/cerberus/pull/42
    * https://github.com/pyeve/eve/issues/295
    """

    class MyValidator(Validator):
        def _validate_root_doc(self, root_doc, field, value):
            """ {'type': 'boolean'} """
            if 'sub' not in self.root_document or len(self.root_document['sub']) != 2:
                self._error(field, 'self.context is not the root doc!')

    schema = {
        'sub': {
            'type': 'list',
            'root_doc': True,
            'itemsrules': {
                'type': 'dict',
                'schema': {'foo': {'type': 'string', 'root_doc': True}},
            },
        }
    }
    assert_success(
        {'sub': [{'foo': 'bar'}, {'foo': 'baz'}]}, validator=MyValidator(schema)
    )


def test_validated(validator):
    validator.schema = {'property': {'type': 'string'}}
    document = {'property': 'string'}
    assert validator.validated(document) == document
    document = {'property': 0}
    assert validator.validated(document) is None


def test_issue_107(validator):
    # https://github.com/pyeve/cerberus/issues/107
    schema = {
        'info': {
            'type': 'dict',
            'schema': {'name': {'type': 'string', 'required': True}},
        }
    }
    document = {'info': {'name': 'my name'}}
    assert_success(document, schema, validator=validator)

    v = Validator(schema)
    assert_success(document, schema, v)
    # it once was observed that this behaves other than the previous line
    assert v.validate(document)


def test_document_path():
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
    assert_success(document, schema, validator=v)


def test_require_all_simple():
    schema = {'foo': {'type': 'string'}}
    validator = Validator(require_all=True)
    assert_fail(
        {},
        schema,
        validator,
        error=('foo', '__require_all__', errors.REQUIRED_FIELD, True),
    )
    assert_success({'foo': 'bar'}, schema, validator)
    validator.require_all = False
    assert_success({}, schema, validator)
    assert_success({'foo': 'bar'}, schema, validator)


def test_require_all_override_by_required():
    schema = {'foo': {'type': 'string', 'required': False}}
    validator = Validator(require_all=True)
    assert_success({}, schema, validator)
    assert_success({'foo': 'bar'}, schema, validator)
    validator.require_all = False
    assert_success({}, schema, validator)
    assert_success({'foo': 'bar'}, schema, validator)

    schema = {'foo': {'type': 'string', 'required': True}}
    validator.require_all = True
    assert_fail(
        {},
        schema,
        validator,
        error=('foo', ('foo', 'required'), errors.REQUIRED_FIELD, True),
    )
    assert_success({'foo': 'bar'}, schema, validator)
    validator.require_all = False
    assert_fail(
        {},
        schema,
        validator,
        error=('foo', ('foo', 'required'), errors.REQUIRED_FIELD, True),
    )
    assert_success({'foo': 'bar'}, schema, validator)


@mark.parametrize(
    "validator_require_all, sub_doc_require_all",
    list(itertools.product([True, False], repeat=2)),
)
def test_require_all_override_by_subdoc_require_all(
    validator_require_all, sub_doc_require_all
):
    sub_schema = {"bar": {"type": "string"}}
    schema = {
        "foo": {
            "type": "dict",
            "require_all": sub_doc_require_all,
            "schema": sub_schema,
        }
    }
    validator = Validator(require_all=validator_require_all)

    assert_success({"foo": {"bar": "baz"}}, schema, validator)
    if validator_require_all:
        assert_fail({}, schema, validator)
    else:
        assert_success({}, schema, validator)
    if sub_doc_require_all:
        assert_fail({"foo": {}}, schema, validator)
    else:
        assert_success({"foo": {}}, schema, validator)


def test_require_all_and_exclude():
    schema = {
        'foo': {'type': 'string', 'excludes': 'bar'},
        'bar': {'type': 'string', 'excludes': 'foo'},
    }
    validator = Validator(require_all=True)
    assert_fail(
        {},
        schema,
        validator,
        errors=[
            ('foo', '__require_all__', errors.REQUIRED_FIELD, True),
            ('bar', '__require_all__', errors.REQUIRED_FIELD, True),
        ],
    )
    assert_success({'foo': 'value'}, schema, validator)
    assert_success({'bar': 'value'}, schema, validator)
    assert_fail({'foo': 'value', 'bar': 'value'}, schema, validator)
    validator.require_all = False
    assert_success({}, schema, validator)
    assert_success({'foo': 'value'}, schema, validator)
    assert_success({'bar': 'value'}, schema, validator)
    assert_fail({'foo': 'value', 'bar': 'value'}, schema, validator)


def test_novalidate_noerrors(validator):
    """
    In v0.1.0 and below `self.errors` raised an exception if no
    validation had been performed yet.
    """
    assert validator.errors == {}
