from __future__ import absolute_import

from collections import Mapping, Sequence

from cerberus.platform import _int_types, _str_type


def compare_paths_lt(x, y):
    for i in range(min(len(x), len(y))):
        if isinstance(x[i], type(y[i])):
            if x[i] != y[i]:
                return x[i] < y[i]
        elif isinstance(x[i], _int_types):
            return True
        elif isinstance(y[i], _int_types):
            return False
    return len(x) < len(y)


def drop_item_from_tuple(t, i):
    return t[:i] + t[i + 1:]


def get_Validator_class():
    global Validator
    if 'Validator' not in globals():
        from cerberus.validator import Validator
    return Validator


def mapping_hash(schema):
    return hash(mapping_to_frozenset(schema))


def mapping_to_frozenset(mapping):
    """ Be aware that this treats any sequence type with the equal members as
        equal. As it is used to identify equality of schemas, this can be
        considered okay as definitions are semantically equal regardless the
        container type. """
    mapping = mapping.copy()
    for key, value in mapping.items():
        if isinstance(value, Mapping):
            mapping[key] = mapping_to_frozenset(value)
        elif isinstance(value, Sequence):
            value = list(value)
            for i, item in enumerate(value):
                if isinstance(item, Mapping):
                    value[i] = mapping_to_frozenset(item)
            mapping[key] = tuple(value)
    return frozenset(mapping.items())


def isclass(obj):
    try:
        issubclass(obj, object)
    except TypeError:
        return False
    else:
        return True


def quote_string(value):
    if isinstance(value, _str_type):
        return '"%s"' % value
    else:
        return value


def validator_factory(name, mixin=None, class_dict={}):
    """ Dynamically create a :class:`~cerberus.Validator` subclass.
        Docstrings of mixin-classes will be added to the resulting
        class' one if ``__doc__`` is not in :obj:`class_dict`.

    :param name: The name of the new class.
    :type name: :class:`str`
    :param mixin: Class(es) with mixin-methods.
    :type mixin: :class:`tuple` of or a single :term:`class`
    :param class_dict: Attributes for the new class.
    :type class_dict: :class:`dict`
    :return: The created class.
    """
    Validator = get_Validator_class()

    if mixin is None:
        bases = (Validator,)
    elif isinstance(mixin, tuple):
        bases = (Validator,) + mixin
    else:
        bases = (Validator, mixin)

    docstrings = [x.__doc__ for x in bases if x.__doc__]
    if len(docstrings) > 1 and '__doc__' not in class_dict:
        class_dict.update({'__doc__': '\n'.join(docstrings)})

    return type(name, bases, class_dict)
