""" This module contains the error-related constants and classes. """

from collections import defaultdict, namedtuple, MutableMapping
from copy import copy
from .utils import compare_paths_lt, quote_string


"""
Error definition constants

Each distinguishable error is defined as a two-value-tuple that holds
a *unique* error id as integer and the rule as string that can cause it.
The attributes are accessible as properties ``id`` and ``rule``.
The names do not contain a common prefix as they are supposed to be referenced
within the module namespace, e.g. errors.CUSTOM
"""

ErrorDefinition = namedtuple('cerberus_error', 'code, rule')

# custom
CUSTOM = ErrorDefinition(0x00, None)

# existence
DOCUMENT_MISSING = ErrorDefinition(0x01, None)  # issues/141
DOCUMENT_MISSING = "document is missing"
REQUIRED_FIELD = ErrorDefinition(0x02, 'required')
UNKNOWN_FIELD = ErrorDefinition(0x03, None)
DEPENDENCIES_FIELD = ErrorDefinition(0x04, 'dependencies')
DEPENDENCIES_FIELD_VALUE = ErrorDefinition(0x05, 'dependencies')
EXCLUDES_FIELD = ErrorDefinition(0x06, 'excludes')

# shape
DOCUMENT_FORMAT = ErrorDefinition(0x21, None)  # issues/141
DOCUMENT_FORMAT = "'{0}' is not a document, must be a dict"
EMPTY_NOT_ALLOWED = ErrorDefinition(0x22, 'empty')
NOT_NULLABLE = ErrorDefinition(0x23, 'nullable')
BAD_TYPE = ErrorDefinition(0x24, 'type')
ITEMS_LENGTH = ErrorDefinition(0x25, 'items')
MIN_LENGTH = ErrorDefinition(0x26, 'minlength')
MAX_LENGTH = ErrorDefinition(0x27, 'maxlength')

# color
REGEX_MISMATCH = ErrorDefinition(0x41, 'regex')
MIN_VALUE = ErrorDefinition(0x42, 'min')
MAX_VALUE = ErrorDefinition(0x43, 'max')
UNALLOWED_VALUE = ErrorDefinition(0x44, 'allowed')
UNALLOWED_VALUES = ErrorDefinition(0x45, 'allowed')
FORBIDDEN_VALUE = ErrorDefinition(0x46, 'forbidden')
FORBIDDEN_VALUES = ErrorDefinition(0x47, 'forbidden')

# other
COERCION_FAILED = ErrorDefinition(0x61, 'coerce')
RENAMING_FAILED = ErrorDefinition(0x62, 'rename_handler')
READONLY_FIELD = ErrorDefinition(0x63, 'readonly')

# groups
ERROR_GROUP = ErrorDefinition(0x80, None)
MAPPING_SCHEMA = ErrorDefinition(0x81, 'schema')
SEQUENCE_SCHEMA = ErrorDefinition(0x82, 'schema')
PROPERTYSCHEMA = ErrorDefinition(0x83, 'propertyschema')
VALUESCHEMA = ErrorDefinition(0x84, 'valueschema')
BAD_ITEMS = ErrorDefinition(0x8f, 'items')

LOGICAL = ErrorDefinition(0x90, None)
NONEOF = ErrorDefinition(0x91, 'noneof')
ONEOF = ErrorDefinition(0x92, 'oneof')
ANYOF = ErrorDefinition(0x93, 'anyof')
ALLOF = ErrorDefinition(0x94, 'allof')


""" SchemaError messages """

SCHEMA_ERROR_DEFINITION_TYPE = \
    "schema definition for field '{0}' must be a dict"
SCHEMA_ERROR_MISSING = "validation schema missing"


""" Error representations """


class ValidationError:
    """ A simple class to store and query basic error information. """
    def __init__(self, document_path, schema_path, code, rule, constraint,
                 value, info):
        self.document_path = document_path
        self.schema_path = schema_path
        self.code = code
        self.rule = rule
        self.constraint = constraint
        self.value = value
        self.info = info

    def __eq__(self, other):
        """ Assumes the errors relate to the same document and schema. """
        return hash(self) == hash(other)

    def __hash__(self):
        """ Expects that all other properties are transitively determined. """
        return hash(self.document_path) ^ hash(self.schema_path) \
            ^ hash(self.code)

    def __lt__(self, other):
        if self.document_path != other.document_path:
            return compare_paths_lt(self.document_path, other.document_path)
        else:
            return compare_paths_lt(self.schema_path, other.schema_path)

    def __repr__(self):
        return "{class_name} @ {memptr} ( " \
               "document_path={document_path}," \
               "schema_path={schema_path}," \
               "code={code}," \
               "constraint={constraint}," \
               "value={value}," \
               "info={info} )"\
               .format(class_name=self.__class__.__name__, memptr=hex(id(self)),  # noqa
                       document_path=self.document_path,
                       schema_path=self.schema_path,
                       code=hex(self.code),
                       constraint=quote_string(self.constraint),
                       value=quote_string(self.value),
                       info=self.info)

    @property
    def child_errors(self):
        """
        A list that contains the individual errors of a bulk validation error.
        """
        return self.info[0] if self.is_group_error else None

    @property
    def definitions_errors(self):
        """ Returns a dictionary with errors mapped to the index of the
            definition it occurred in. Returns ``None`` if not applicable. """
        if not self.is_logic_error:
            return None

        result = defaultdict(list)
        for error in self.child_errors:
            i = error.schema_path[len(self.schema_path)]
            result[i].append(error)
        return result

    @property
    def is_group_error(self):
        """ ``True`` for errors of bulk validations. """
        return bool(self.code & ERROR_GROUP.code)

    @property
    def is_logic_error(self):
        """ ``True`` for validation errors against different schemas. """
        return bool(self.code & LOGICAL.code - ERROR_GROUP.code)


class ErrorsList(list):
    def __contains__(self, error_definition):
        for code in (x.code for x in self):
            if code == error_definition.code:
                return True
        return False


class ErrorTreeNode(MutableMapping):
    __slots__ = ('descendants', 'errors', 'parent_node', 'path', 'tree_root')

    def __init__(self, path, parent_node):
        self.parent_node = parent_node
        self.tree_root = self.parent_node.tree_root
        self.path = path[:len(self.parent_node.path) + 1]
        self.errors = ErrorsList()
        self.descendants = {}

    def __add__(self, error):
        self.add(error)
        return self

    def __delitem__(self, key):
        del self.descendants[key]

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, item):
        if item in self.descendants:
            return self.descendants[item]
        else:
            return None

    def __len__(self):
        return len(self.errors)

    def __setitem__(self, key, value):
        self.descendants[key] = value

    def __str__(self):
        return str(self.errors) + ',' + str(self.descendants)

    @property
    def depth(self):
        return len(self.path)

    @property
    def tree_type(self):
        return self.parent_node.tree_type

    def _path_of_(self, error):
        return getattr(error, self.tree_type + '_path')

    def add(self, error):
        error_path = self._path_of_(error)

        key = error_path[self.depth]
        if key not in self.descendants:
            self[key] = ErrorTreeNode(error_path, self)

        if len(error_path) == self.depth + 1:
            self[key].errors.append(error)
            self[key].errors.sort()
            if error.is_group_error:
                for child_error in error.info[0]:
                    self.tree_root += child_error
        else:
            self[key] += error


class ErrorTree(ErrorTreeNode):
    def __init__(self, errors=[]):
        self.parent_node = None
        self.tree_root = self
        self.path = ()
        self.errors = []
        self.descendants = {}
        for error in errors:
            self += error

    def add(self, error):
        if not self._path_of_(error):
            self.errors.append(error)
            self.errors.sort()
        else:
            super(ErrorTree, self).add(error)

    def fetch_errors_from(self, path):
        """ Returns all errors for a particular path.
        :param path: Tuple of hashables.
        """
        node = self.fetch_node_from(path)
        if node is not None:
            return node.errors
        else:
            return []

    def fetch_node_from(self, path):
        """ Returns a node for a path or ``None``.
        :param path:  Tuple of hashables.
        """
        context = self
        for key in path:
            context = context[key]
            if context is None:
                return None
        return context


class DocumentErrorTree(ErrorTree):
    """ Implements a dict-like class to query errors by indexes following the
        structure of a validated document. """
    tree_type = 'document'


class SchemaErrorTree(ErrorTree):
    """ Implements a dict-like class to query errors by indexes following the
        structure of the used schema. """
    tree_type = 'schema'


class BaseErrorHandler:
    """ Base class for all error handlers.
        Subclasses are identified as error-handlers with an instance-test. """
    def __init__(self, *args, **kwargs):
        """ Optionally initialize a new instance. """
        pass

    def __call__(self, errors):
        """ Returns errors in a handler-specific format.
            Should accept an iterable of :class:`ValidationError` or a
            :class:`~cerberus.Validator` instance."""
        raise NotImplementedError

    def __iter__(self):
        """ Be a superhero and implement an iterator over errors. """
        raise NotImplementedError

    def add(self, error):
        """ Add an error to the errors' container object of a handler. """
        raise NotImplementedError

    def emit(self, error):
        """ Optionally emits an error in the handler's format to a stream.
            Or light a LED, or even shut down a power plant. """
        pass

    def end(self, validator):
        """ Gets called when a validation ends. """
        pass

    def extend(self, errors):
        """ Adds all errors to the handler's container object. """
        for error in errors:
            self.add(error)

    def start(self, validator):
        """ Gets called when a validation starts. """
        pass


class ToyErrorHandler(BaseErrorHandler):
    def __call__(self, *args, **kwargs):
        raise RuntimeError('This is not supposed to happen.')

    def clear(self):
        pass


class BasicErrorHandler(BaseErrorHandler):
    """ Models cerberus' legacy. Returns a dictionary. """
    messages = {0x00: "{0}",

                0x01: "document is missing",
                0x02: "required field",
                0x03: "unknown field",
                0x04: "field '{0}' is required",
                0x05: "depends on these values: {constraint}",
                0x06: "{0} must not be present with '{field}'",

                0x21: "'{0}' is not a document, must be a dict",
                0x22: "empty values not allowed",
                0x23: "null value not allowed",
                0x24: "must be of {constraint} type",
                0x25: "length of list should be {constraint}, it is {0}",
                0x26: "min length is {constraint}",
                0x27: "max length is {constraint}",

                0x41: "value does not match regex '{constraint}'",
                0x42: "min value is {constraint}",
                0x43: "max value is {constraint}",
                0x44: "unallowed value {value}",
                0x45: "unallowed values {0}",
                0x46: "unallowed value {value}",
                0x47: "unallowed values {0}",

                0x61: "field '{field}' cannot be coerced: {0}",
                0x62: "field '{field}' cannot be renamed: {0}",
                0x63: "field is read-only",

                0x81: "mapping doesn't validate subschema: {0}",
                0x82: "one or more sequence-items don't validate: {0}",
                0x83: "one or more properties of a mapping  don't validate: "
                      "{0}",
                0x84: "one or more values in a mapping don't validate: {0}",
                0x85: "one or more sequence-items don't validate: {0}",

                0x91: "one or more definitions validate",
                0x92: "none or more than one rule validate",
                0x93: "no definitions validate",
                0x94: "one or more definitions don't validate"
                }

    def __init__(self, tree=None):
        self.tree = {} if tree is None else tree

    def __call__(self, errors=None):
        if errors is not None:
            self.clear()
            self.extend(errors)
        return self.tree

    def add(self, error):
        if error.code not in self.messages and not error.is_group_error:
            return
        elif error.is_group_error:
            self.insert_group_error(error)
        else:
            field = error.document_path[-1] if error.document_path else None
            self.insert_error(error.document_path,
                              self.format_message(field, error))

    def clear(self):
        self.tree = {}

    def format_message(self, field, error):
        return self.messages[error.code]\
            .format(*error.info, constraint=error.constraint,
                    field=field, value=error.value)

    def insert_error(self, path, node):
        """ Adds an error or sub-tree to :attr:tree.

        :param path: Path to the error.
        :type path: Tuple of strings and integers.
        :param node: An error message or a sub-tree.
        :type node: String or dictionary.
        """
        if len(path) == 1:
            field = path[0]
            if field in self.tree:
                if isinstance(self.tree[field], list):
                    self.tree[field].append(node)
                else:
                    self.tree[field] = [self.tree[field], node]
            else:
                self.tree[field] = node
        elif len(path) >= 1:
            if path[0] in self.tree:
                new = self.__class__(tree=copy(self.tree[path[0]]))
                new.insert_error(path[1:], node)
                self.tree[path[0]].update(new.tree)
            else:
                child_handler = self.__class__()
                child_handler.insert_error(path[1:], node)
                self.tree[path[0]] = child_handler.tree

    def insert_group_error(self, error):
        if error.is_logic_error:
            self.insert_logic_error(error)

        for error in error.child_errors:
            if error.is_group_error:
                self.insert_group_error(error)
            else:
                field = error.document_path[-1] if error.document_path else None
                self.insert_error(error.document_path,
                                  self.format_message(field, error))

    def insert_logic_error(self, error):
        path = error.document_path + (error.rule, )
        self.insert_error(path, self.format_message(None, error))
        for i in error.definitions_errors:
            for child_error in error.definitions_errors[i]:
                field = child_error.document_path[-1]
                path = child_error.document_path[:-1] + \
                    ('definition % s' % i, field)
                self.insert_error(path, self.format_message(field, child_error))  # noqa

    def start(self, validator):
        self.clear()


class SchemaErrorHandler(BasicErrorHandler):
    messages = BasicErrorHandler.messages.copy()
    messages[0x03] = "unknown rule"
