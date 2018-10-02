from typing import Tuple


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


def drop_item_from_tuple(t: Tuple, i: int) -> Tuple:
    return t[:i] + t[i + 1 :]


def quote_string(value: str) -> str:
    if isinstance(value, str):
        return '"%s"' % value
    else:
        return value


class readonly_classproperty(property):
    def __get__(self, instance, owner):  # type: ignore
        return super().__get__(owner)

    def __set__(self, instance, value):  # type: ignore
        raise RuntimeError('This is a readonly class property.')

    def __delete__(self, instance):  # type: ignore
        raise RuntimeError('This is a readonly class property.')
