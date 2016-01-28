from .platform import _int_types, _str_type


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


def validator_factory(name, mixin=None, class_dict=dict()):
    if 'Validator' not in globals():
        from .cerberus import Validator

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
