# -*- coding: utf-8 -*-

from copy import deepcopy
from pkg_resources import Distribution, DistributionNotFound

import pytest

from cerberus import Validator


def reload_module(name):
    try:
        reload
    except NameError:
        try:
            from importlib import reload
        except ImportError:
            from imp import reload
    reload(name)


@pytest.fixture
def cerberus():
    return __import__('cerberus')


@pytest.fixture(scope="function")
def get_distribution_finds_distribution(monkeypatch, cerberus):
    def creates_distribution(name):
        return Distribution(project_name="cerberus", version="1.2.3")

    with monkeypatch.context() as m:
        m.setattr('pkg_resources.get_distribution', creates_distribution)
        reload_module(cerberus)


@pytest.fixture
def get_distribution_raises_exception(monkeypatch, cerberus):
    def raise_distribution_not_found(name):
        raise DistributionNotFound("pkg_resources cannot get distribution")

    with monkeypatch.context() as m:
        m.setattr('pkg_resources.get_distribution', raise_distribution_not_found)
        reload_module(cerberus)


@pytest.fixture
def document():
    return deepcopy(sample_document)


@pytest.fixture
def schema():
    return deepcopy(sample_schema)


@pytest.fixture
def validator():
    return Validator(sample_schema)


sample_schema = {
    'a_string': {'type': 'string', 'minlength': 2, 'maxlength': 10},
    'a_binary': {'type': 'binary', 'minlength': 2, 'maxlength': 10},
    'a_nullable_integer': {'type': 'integer', 'nullable': True},
    'an_integer': {'type': 'integer', 'min': 1, 'max': 100},
    'a_restricted_integer': {'type': 'integer', 'allowed': [-1, 0, 1]},
    'a_boolean': {'type': 'boolean', 'meta': 'can haz two distinct states'},
    'a_datetime': {'type': 'datetime', 'meta': {'format': '%a, %d. %b %Y'}},
    'a_float': {'type': 'float', 'min': 1, 'max': 100},
    'a_number': {'type': 'number', 'min': 1, 'max': 100},
    'a_set': {'type': 'set'},
    'one_or_more_strings': {'type': ['string', 'list'], 'schema': {'type': 'string'}},
    'a_regex_email': {
        'type': 'string',
        'regex': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
    },
    'a_readonly_string': {'type': 'string', 'readonly': True},
    'a_restricted_string': {'type': 'string', 'allowed': ['agent', 'client', 'vendor']},
    'an_array': {'type': 'list', 'allowed': ['agent', 'client', 'vendor']},
    'an_array_from_set': {
        'type': 'list',
        'allowed': set(['agent', 'client', 'vendor']),
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
        'items': [{'type': 'string'}, {'type': 'integer'}],
    },
    'a_list_of_integers': {'type': 'list', 'schema': {'type': 'integer'}},
    'a_dict': {
        'type': 'dict',
        'schema': {
            'address': {'type': 'string'},
            'city': {'type': 'string', 'required': True},
        },
    },
    'a_dict_with_valuesrules': {'type': 'dict', 'valuesrules': {'type': 'integer'}},
    'a_list_length': {
        'type': 'list',
        'schema': {'type': 'integer'},
        'minlength': 2,
        'maxlength': 5,
    },
    'a_nullable_field_without_type': {'nullable': True},
    'a_not_nullable_field_without_type': {},
}

sample_document = {'name': 'john doe'}
