""" Platform-dependent objects """

import sys


if sys.version_info < (3, 7):
    from typing import _ForwardRef as ForwardRef
    from typing import GenericMeta as _GenericAlias
    from typing import _Union, Union

    def get_type_args(tp):
        if isinstance(tp, (_GenericAlias, _Union)):
            return tp.__args__
        return ()

    def get_type_origin(tp):
        if isinstance(tp, _GenericAlias):
            return tp.__extra__
        if isinstance(tp, _Union):
            return Union
        return None


elif sys.version_info < (3, 8):
    from typing import ForwardRef, _GenericAlias  # type: ignore

    def get_type_args(tp):
        if isinstance(tp, _GenericAlias):
            return tp.__args__
        return ()

    def get_type_origin(tp):
        if isinstance(tp, _GenericAlias):
            return tp.__origin__
        return None


else:
    from typing import ForwardRef, _GenericAlias
    from typing import get_args as get_type_args
    from typing import get_origin as get_type_origin


__all__ = (
    "ForwardRef",
    "_GenericAlias",
    get_type_args.__name__,
    get_type_origin.__name__,
)
