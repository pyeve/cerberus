"""
    Mocking support for dictionaries defined by cerberus schema.
"""

from collections import MutableMapping
from cerberus import Validator, ValidationError


class CerberusMock(MutableMapping):

    def __init__(self, schema, document=None, create_missing=False):
        """
        :param schema: The cerberus schema that this mock object will enforce.
        :param document: Any pre-existing content this mock should have.
        :param create_missing: Even if parameters are not required, initialise
                them to a sensible default.
        """
        self.schema = schema
        self._document = document or self._create_blank_from_schema(
            schema, create_missing)
        self._validator = Validator(schema)
        if not self._validator.validate(self._document):
            key, error = next(iter(self._validator.errors.items()))
            raise ValidationError('{}: {}'.format(key, error))

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self._document)

    def __getitem__(self, key):
        return self._document[key]

    def __setitem__(self, key, value):
        self._document[key] = value

    def __delitem__(self, key):
        del self._document[key]

    def __iter__(self):
        return iter(self._document)

    def __len__(self):
        return len(self._document)

    @classmethod
    def _create_blank_from_schema(cls, schema, create_missing):
        new_doc = {}
        for key, constraints in schema.items():
            if constraints.get('required') or create_missing:
                factory = getattr(
                    cls, '_{}_from_constraints'.format(constraints['type']))
                new_doc[key] = factory(constraints)
        return new_doc

    @classmethod
    def _string_from_constraints(cls, constraints):
        min_length = constraints.get('minlength', 0)
        return '*' * min_length
