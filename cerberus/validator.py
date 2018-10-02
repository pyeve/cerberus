"""
    Extensible validation for Python dictionaries.
    This module implements Cerberus Validator class

    :copyright: 2012-2016 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at http://python-cerberus.org
"""

from cerberus.base import UnconcernedValidator
from cerberus.schema import ValidatedSchema


class Validator(UnconcernedValidator):
    def __init_schema(self, schema):
        if schema is not None:
            self.schema = ValidatedSchema(self, schema)

    @property
    def allow_unknown(self):
        """ If ``True`` unknown fields that are not defined in the schema will
            be ignored. If a mapping with a validation schema is given, any
            undefined field will be validated against its rules.
            Also see :ref:`allowing-the-unknown`.
            Type: :class:`bool` or any :term:`mapping` """
        return self._config.get('allow_unknown', False)

    @allow_unknown.setter
    def allow_unknown(self, value):
        if not (self.is_child or isinstance(value, (bool, ValidatedSchema))):
            ValidatedSchema(self, {'allow_unknown': value})
        self._config['allow_unknown'] = value

    @property
    def schema(self):
        """ The validation schema of a validator. When a schema is passed to
            a method, it replaces this attribute.
            Type: any :term:`mapping` or :obj:`None` """
        return self._schema

    @schema.setter
    def schema(self, schema):
        if schema is None:
            self._schema = None
        elif self.is_child or isinstance(schema, ValidatedSchema):
            self._schema = schema
        else:
            self._schema = ValidatedSchema(self, schema)
