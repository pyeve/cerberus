""" Platform-dependent objects """

import sys


if sys.version_info < (3, 7):
    from typing import _ForwardRef as ForwardRef  # noqa: F401
    from typing import GenericMeta as _GenericAlias  # noqa: F401

    TYPE_ALIAS_ORIGIN_ATTRIBUTE = "__extra__"

else:
    from typing import ForwardRef  # type: ignore  # noqa: F401
    from typing import _GenericAlias  # type: ignore  # noqa: F401

    TYPE_ALIAS_ORIGIN_ATTRIBUTE = "__origin__"
