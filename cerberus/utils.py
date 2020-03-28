from collections import abc
from typing import Dict, Hashable, Mapping, Sequence, Set


def compare_paths_lt(x, y):
    min_length = min(len(x), len(y))

    if x[:min_length] == y[:min_length]:
        return len(x) == min_length

    for i in range(min_length):
        a, b = x[i], y[i]

        for _type in (int, str, tuple):
            if isinstance(a, _type):
                if isinstance(b, _type):
                    break
                else:
                    return True

        if a == b:
            continue
        elif a < b:
            return True
        else:
            return False

    raise RuntimeError


def drop_item_from_tuple(t, i):
    return t[:i] + t[i + 1 :]


def mapping_to_frozenset(schema: Mapping) -> frozenset:
    """ Be aware that this treats any sequence type with the equal members as
        equal. As it is used to identify equality of schemas, this can be
        considered okay as definitions are semantically equal regardless the
        container type. """
    schema_copy = {}  # type: Dict[Hashable, Hashable]
    for key, value in schema.items():
        if isinstance(value, abc.Mapping):
            schema_copy[key] = mapping_to_frozenset(value)
        elif isinstance(value, Sequence):
            value = list(value)
            for i, item in enumerate(value):
                if isinstance(item, abc.Mapping):
                    value[i] = mapping_to_frozenset(item)
            schema_copy[key] = tuple(value)
        elif isinstance(value, Set):
            schema_copy[key] = frozenset(value)
        elif isinstance(value, Hashable):
            schema_copy[key] = value
        else:
            raise TypeError("All schema contents must be hashable.")

    return frozenset(schema_copy.items())


def quote_string(value):
    if isinstance(value, str):
        return '"%s"' % value
    else:
        return value


class readonly_classproperty(property):
    def __get__(self, instance, owner):
        return super().__get__(owner)

    def __set__(self, instance, value):
        raise RuntimeError('This is a readonly class property.')

    def __delete__(self, instance):
        raise RuntimeError('This is a readonly class property.')


def schema_hash(schema: Mapping) -> int:
    return hash(mapping_to_frozenset(schema))
