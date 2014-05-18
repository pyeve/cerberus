"""
    Mocking support for dictionaries defined by cerberus schema.
"""

import re
import string
from collections import MutableMapping, MutableSequence
from datetime import datetime
from cerberus import Validator, ValidationError


class CerberusMock(MutableMapping):

    _type_name_mapping = {
        'boolean': bool,
        'set': set,
    }

    def __init__(self, schema, document=None, create_missing=False, **kwargs):
        """
        :param schema: The cerberus schema that this mock object will enforce.
        :param document: Any pre-existing content this mock should have.
        :param create_missing: Even if parameters are not required, initialise
                them to a sensible default.
        """
        self.schema = schema
        self._document = document or self._create_blank_from_schema(
            schema, create_missing)
        self._validator = Validator(schema, **kwargs)
        self._validate_and_raise(self._document)

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self._document)

    def __getitem__(self, key):
        return self._document[key]

    def __setitem__(self, key, value):
        self._validate_and_raise({key: value}, update=True)
        item_schema = self.schema[key].get('schema')
        if isinstance(value, MutableMapping):
            keyschema = self.schema[key].get('keyschema')
            if keyschema:
                value = CerberusKeySchemaMock(keyschema, value)
            else:
                value = self.__class__(item_schema, value)
        elif isinstance(value, MutableSequence):
            value = [
                self.__class__(item_schema['schema'], i) if
                isinstance(i, MutableMapping) else i for i in value]
        self._document[key] = value

    def __delitem__(self, key):
        self._document[key]  # Die if key missing
        constraints = self.schema[key]
        if constraints.get('readonly'):
            raise ValidationError(
                "Can't delete read-only field {0!r}".format(key))
        elif constraints.get('required'):
            raise ValidationError(
                "Can't delete required field {0!r}".format(key))
        else:
            del self._document[key]

    def __iter__(self):
        return iter(self._document)

    def __len__(self):
        return len(self._document)

    def _validate_and_raise(self, *args, **kwargs):
        if not self._validator.validate(*args, **kwargs):
            key, error = next(iter(self._validator.errors.items()))
            raise ValidationError('{0}: {1}'.format(key, error))

    @classmethod
    def _create_blank_from_schema(cls, schema, create_missing):
        new_doc = {}
        for key, constraints in schema.items():
            if constraints.get('required') or create_missing:
                new_doc[key] = cls._value_from_constraints(constraints)
        return new_doc

    @classmethod
    def _value_from_constraints(cls, constraints):
        if constraints.get('nullable'):
            return None
        type_name = constraints.get('type')
        if type_name:
            try:
                factory = getattr(
                    cls, '_{0}_from_constraints'.format(type_name))
            except AttributeError:
                factory = cls._type_name_mapping[type_name]
                return factory()
            else:
                return factory(constraints)
        else:
            # Typeless, not-nullable field
            return ''

    @classmethod
    def _string_from_constraints(cls, constraints):
        allowed = constraints.get('allowed')
        regex = constraints.get('regex')
        if allowed:
            return allowed[0]
        elif regex:
            new_string = _make_matching_string_from_regex(regex)
        else:
            min_length = constraints.get('minlength', 0)
            new_string = 'a' * min_length
        return new_string

    @classmethod
    def _list_from_constraints(cls, constraints):
        items_constraints = constraints.get('items')
        schema = constraints.get('schema')
        allowed = constraints.get('allowed')
        min_length = constraints.get('minlength', 0)
        if isinstance(items_constraints, dict):
            # deprecated list of dicts
            dict_constraints = {'type': 'dict', 'schema': items_constraints}
            return [cls._dict_from_constraints(dict_constraints)]
        elif items_constraints:
            return [cls._value_from_constraints(c) for c in items_constraints]
        elif schema:
            return [cls._value_from_constraints(schema)] * min_length
        elif allowed:
            return [allowed[0]] * min_length
        else:
            return []

    @classmethod
    def _dict_from_constraints(cls, constraints):
        keyschema = constraints.get('keyschema')
        if keyschema:
            return CerberusKeySchemaMock(keyschema)
        else:
            schema = constraints.get('schema', {})
            return cls(schema)

    @classmethod
    def _integer_from_constraints(cls, constraints):
        allowed = constraints.get('allowed')
        if allowed:
            return allowed[0]
        else:
            return constraints.get('min', 0)
    _number_from_constraints = _integer_from_constraints

    @classmethod
    def _float_from_constraints(cls, constraints):
        return float(constraints.get('min', 0))

    @classmethod
    def _datetime_from_constraints(cls, constraints):
        return datetime.fromtimestamp(0)


class CerberusKeySchemaMock(MutableMapping):
    def __init__(self, keyschema, document=None):
        self.keyschema = keyschema
        self._document = {}
        self._validator = Validator()
        if document:
            self.update(document)

    def __getitem__(self, key):
        return self._document[key]

    def __setitem__(self, key, value):
        if self._validator.validate(
                {key: value}, schema={key: self.keyschema}):
            self._document[key] = value
        else:
            key, error = next(iter(self._validator.errors.items()))
            raise ValidationError('{0}: {1}'.format(key, error))

    def __delitem__(self, key):
        del self._document[key]

    def __len__(self):
        return len(self._document)

    def __iter__(self):
        return iter(self._document)


def _traverse_regex(tree):
    """ Courtesy of StackOverflow:
    http://stackoverflow.com/questions/492716/reversing-a-regular-expression\
-in-python
    """
    retval = ''
    for node in tree:
        if node[0] == 'any':
            retval += 'x'
        elif node[0] == 'at':
            pass
        elif node[0] in ['min_repeat', 'max_repeat']:
            retval += _traverse_regex(node[1][2]) * node[1][0]
        elif node[0] == 'in':
            if node[1][0][0] == 'negate':
                letters = list(string.ascii_letters)
                for part in node[1][1:]:
                    if part[0] == 'literal':
                        letters.remove(chr(part[1]))
                    else:
                        for letter in range(part[1][0], part[1][1] + 1):
                            letters.remove(chr(letter))
                retval += letters[0]
            else:
                if node[1][0][0] == 'range':
                    retval += chr(node[1][0][1][0])
                else:
                    retval += chr(node[1][0][1])
        elif node[0] == 'not_literal':
            if node[1] == 120:
                retval += 'y'
            else:
                retval += 'x'
        elif node[0] == 'branch':
            retval += _traverse_regex(node[1][1][0])
        elif node[0] == 'subpattern':
            retval += _traverse_regex(node[1][1])
        elif node[0] == 'literal':
            retval += chr(node[1])
    return retval


def _make_matching_string_from_regex(regex):
    return _traverse_regex(re.sre_parse.parse(regex).data)
