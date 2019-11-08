from cerberus import Validator


def test_validated_schema_cache():
    v = Validator({'foozifix': {'coerce': int}})
    cache_size = len(v._valid_schemas)

    v = Validator({'foozifix': {'type': 'integer'}})
    cache_size += 1
    assert len(v._valid_schemas) == cache_size

    v = Validator({'foozifix': {'coerce': int}})
    assert len(v._valid_schemas) == cache_size

    max_cache_size = 427
    assert cache_size <= max_cache_size, (
        "There's an unexpected high amount (%s) of cached valid definition schemas. "
        "Unless you added further tests, there are good chances that something is "
        "wrong. If you added tests with new schemas, you can try to adjust the "
        "variable `max_cache_size` according to the added schemas." % cache_size
    )
