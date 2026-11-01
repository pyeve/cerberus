import copy
from cerberus.utils import compare_paths_lt, mapping_hash


def test_compare_paths():
    lesser = ('a_dict', 'keysrules')
    greater = ('a_dict', 'valuesrules')
    assert compare_paths_lt(lesser, greater)

    lesser += ('type',)
    greater += ('regex',)
    assert compare_paths_lt(lesser, greater)


def test_mapping_to_frozenset_with_nested_containers():
    # A schema may allow values that are themselves containers, e.g. a list of
    # pairs. Those are not hashable, and building the hash used to raise
    # TypeError: unhashable type: 'list' before any validation happened.
    schema = {'f': {'type': 'list', 'allowed': [[1, 2], [3, 4]]}}
    assert mapping_hash(schema) == mapping_hash(copy.deepcopy(schema))
    # a list and a tuple with the same members describe the same schema
    assert mapping_hash({'f': {'allowed': [[1, 2]]}}) == mapping_hash({
        'f': {'allowed': [(1, 2)]}
    })
    # and so do a set and the matching frozenset
    assert mapping_hash({'f': {'allowed': [{1, 2}]}}) == mapping_hash({
        'f': {'allowed': [frozenset({1, 2})]}
    })
    assert mapping_hash({'f': {'allowed': [[1, 2]]}}) != mapping_hash({
        'f': {'allowed': [[1, 3]]}
    })
