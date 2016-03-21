from collections import Mapping

from .platform import _int_types, _str_type


def cast_keys_to_strings(mapping):
    result = {}
    for key in mapping:
        if isinstance(mapping[key], Mapping):
            value = cast_keys_to_strings(mapping[key])
        else:
            value = mapping[key]
        result[str(type(key)) + str(key)] = value
    return result


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
    if 'Validator' not in globals():
        from .cerberus import Validator
    return Validator


def validator_factory(name, mixin=None, class_dict={}):
    """ Dynamically create a :class:`~cerberus.Validator` subclass.

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

    return type(name, bases, class_dict)


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
