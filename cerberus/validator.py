"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2016 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
"""
from typing import ClassVar, Optional, Set, Tuple  # noqa: F401

from cerberus.base import UnconcernedValidator
from cerberus.schema import ValidatedSchema
from cerberus.typing import AllowUnknown, Schema


class Validator(UnconcernedValidator):
    _valid_schemas = set()  # type: ClassVar[Set[Tuple[int, int]]]
    """ A :class:`set` of hash tuples derived from validation schemas and the types
        mapping of the validator that are legit to use. """

    def __init_schema(self, schema):
        if schema is not None:
            self.schema = ValidatedSchema(self, schema)

    @property
    def allow_unknown(self) -> AllowUnknown:
        """ If ``True`` unknown fields that are not defined in the schema will
            be ignored. If a mapping with a validation schema is given, any
            undefined field will be validated against its rules.
            Also see :ref:`allowing-the-unknown`. """
        return self._config.get('allow_unknown', False)

    @allow_unknown.setter
    def allow_unknown(self, value: AllowUnknown) -> None:
        if not (self.is_child or isinstance(value, (bool, ValidatedSchema))):
            ValidatedSchema(self, {'allow_unknown': value})
        self._config['allow_unknown'] = value

    @property  # type: ignore
    def schema(self):
        """ The validation schema of a validator. When a schema is passed to
            a method, it replaces this attribute. """
        return self._schema

    @schema.setter
    def schema(self, schema: Optional[Schema]) -> None:
        if schema is None:
            self._schema = None
        elif self.is_child or isinstance(schema, ValidatedSchema):
            self._schema = schema
        else:
            self._schema = ValidatedSchema(self, schema)
