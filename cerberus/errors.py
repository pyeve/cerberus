""" This module contains the error-related constants and classes. """

from copy import copy

# custom
CUSTOM = 0x00, None

# existence
DOCUMENT_MISSING = 0x01, None  # issues/141
DOCUMENT_MISSING = "document is missing"
REQUIRED_FIELD = 0x02, 'required'
UNKNOWN_FIELD = 0x03, None
DEPENDENCIES_FIELD = 0x04, 'dependencies'
DEPENDENCIES_FIELD_VALUE = 0x05, 'dependencies'
EXCLUDES_FIELD = 0x06, 'excludes'

# shape
DOCUMENT_FORMAT = 0x21, None  # issues/141
DOCUMENT_FORMAT = "'{0}' is not a document, must be a dict"
EMPTY_NOT_ALLOWED = 0x22, 'empty'
NOT_NULLABLE = 0x23, 'nullable'
UNKNOWN_TYPE = 0x24, 'type'  # REMOVE?
BAD_TYPE = 0x25, 'type'
ITEMS_LENGTH = 0x26, 'items'
MIN_LENGTH = 0x27, 'minlength'
MAX_LENGTH = 0x28, 'maxlength'

# color
REGEX_MISMATCH = 0x41, 'regex'
MIN_VALUE = 0x42, 'min'
MAX_VALUE = 0x43, 'max'
UNALLOWED_VALUE = 0x44, 'allowed'
UNALLOWED_VALUES = 0x45, 'allowed'

# other
COERCION_FAILED = 0x61, 'coerce'
READONLY_FIELD = 0x62, 'readonly'

# groups
ERROR_GROUP = 0x80, None
MAPPING_SCHEMA = 0x81, 'schema'
SEQUENCE_SCHEMA = 0x82, 'schema'
PROPERTYSCHEMA = 0x83, 'propertyschema'
VALUESCHEMA = 0x84, 'valueschema'
BAD_ITEMS = 0x8f, 'items'

LOGICAL = 0x90, None
NONEOF = 0x91, 'noneof'
ONEOF = 0x92, 'oneof'
ANYOF = 0x93, 'anyof'
ALLOF = 0x94, 'allof'


SCHEMA_ERROR_ALLOW_UNKNOWN_TYPE = \
    "allow_unknown-definition for field '{0}' must be a bool or a dict"
SCHEMA_ERROR_CALLABLE_TYPE = \
    "coerce- and validator-definitions for field '{0}' must be a callable"
SCHEMA_ERROR_CONSTRAINT_TYPE = "the constraint for field '{0}' must be a dict"
SCHEMA_ERROR_DEFINITION_SET_TYPE = \
    "definitions of '{0}' for field '{1}' must be a sequence of constraints"
SCHEMA_ERROR_DEFINITION_TYPE = \
    "schema definition for field '{0}' must be a dict"
SCHEMA_ERROR_DEPENDENCY_TYPE = \
    "dependency-definition for field '{0}' must be a dict or a list"
SCHEMA_ERROR_DEPENDENCY_VALIDITY = \
    "'{0}' is no valid dependency for field '{1}'"
SCHEMA_ERROR_EXCLUDES_HASHABLE = "{0} is not hashable ; cannot be excluded"
SCHEMA_ERROR_MISSING = "validation schema missing"
SCHEMA_ERROR_PURGE_UNKNOWN_TYPE = \
    "purge_unknown-definition for field '{0}' must be a bool"
SCHEMA_ERROR_RENAME_TYPE = "rename-definition for field '{0}' must be hashable"
SCHEMA_ERROR_TYPE_TYPE = "type of field '{0}' must be either 'list' or 'dict'"
SCHEMA_ERROR_UNKNOWN_RULE = "unknown rule '{0}' for field '{0}'"
SCHEMA_ERROR_UNKNOWN_TYPE = "unrecognized data-type '{0}'"


class ValidationError:
    # TODO docstring
    # TODO implement __lt__ for sorting?
    def __init__(self, document_path, schema_path, code, rule, constraint,
                 value, info):
        self.document_path = document_path
        self.schema_path = schema_path
        self.code = code
        self.rule = rule
        self.constraint = constraint
        self.value = value
        self.info = info

    def __repr__(self):
        # FIXME display strings quoted
        return "{class_name} @ {memptr} ( " \
               "document_path={document_path}," \
               "schema_path={schema_path}," \
               "code={code}," \
               "constraint={constraint}," \
               "value={value}" \
               "info={info} )"\
               .format(class_name=self.__class__.__name__, memptr=hex(id(self)),  # noqa
                       document_path=self.document_path,
                       schema_path=self.schema_path,
                       code=hex(self.code),
                       constraint=self.constraint,
                       value=self.value,
                       info=self.info)

    @property
    def child_errors(self):
        if self.is_group_error:
            return self.info[0]
        else:
            return None

    @property
    def is_group_error(self):
        return bool(self.code & ERROR_GROUP[0])

    @property
    def is_logic_error(self):
        return bool(self.code & LOGICAL[0] - ERROR_GROUP[0])


class BaseErrorHandler:
    """ Subclasses can be identified as error-handlers with an
        instance-test. """
    def __init__(self):
        """ Optionally initialize a new instance. """
        pass

    def __call__(self, errors):
        """ Returns errors in a handler-specific format. """
        raise NotImplementedError

    def __iter__(self):
        """ Be a superhero and implement a stream of errors. """
        raise NotImplementedError


# FIXME rename to LegacyErrorHandler?
class BasicErrorHandler(BaseErrorHandler):
    """ An error-handler that models cerberus' unhandled legacy. """
    messages = {0x00: "{0}",

                0x01: "document is missing",
                0x02: "required field",
                0x03: "unknown field",
                0x04: "field '{0}' is required by field '{field}",
                0x05: "'{field}' depends on these values: {constraint}",
                0x06: "{0} must not be present with '{field}'",

                0x21: "'{0}' is not a document, must be a dict",
                0x22: "empty values not allowed",
                0x23: "null value not allowed",
                0x24: "unrecognized data-type '{0}'",  # REMOVE?
                0x25: "must be of {constraint} type",
                0x26: "length of list should be {0}, it is {1}",
                0x27: "min length is {constraint}",
                0x28: "max length is {constraint}",

                0x41: "value does not match regex '{constraint}'",
                0x42: "min value is {constraint}",
                0x43: "max value is {constraint}",
                0x44: "unallowed value {value}",
                0x45: "unallowed values {0}",

                0x61: "field '{field}' cannot be coerced",
                0x62: "field is read-only",

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

    def __init__(self, **kwargs):
        self.tree = kwargs.get('tree', dict())
        assert isinstance(self.tree, dict)

    def __call__(self, errors):
        for error in errors:
            if error.code not in self.messages and \
                    not error.is_group_error:
                continue

            field = error.document_path[-1] if error.document_path else None

            if error.is_group_error:
                self.insert_group_error(error)
            else:
                self.insert_error(error.document_path,
                                  self.format_message(field, error))

        return self.tree

    def format_message(self, field, error):
        return self.messages[error.code]\
            .format(*error.info, constraint=error.constraint,
                    field=field, value=error.value)

    def insert_error(self, path, node):
        assert isinstance(path, (tuple, list))
        if len(path) == 1:
            field = path[0]
            # FIXME figure out why second condition is necessary, be sober
            if field in self.tree and node != self.tree[field]:
                if isinstance(self.tree[field], list):
                    self.tree[field].append(node)
                else:
                    self.tree[field] = [self.tree[field], node]
            else:
                self.tree[field] = node
        elif len(path) >= 1:
            if path[0] in self.tree:
                assert isinstance(self.tree[path[0]], dict)
                new = BasicErrorHandler(tree=copy(self.tree[path[0]]))
                new.insert_error(path[1:], node)
                self.tree[path[0]].update(new.tree)
            else:
                child_handler = BasicErrorHandler()
                child_handler.insert_error(path[1:], node)
                self.tree[path[0]] = child_handler.tree

    def insert_group_error(self, error):
        if error.is_logic_error:
            return self.insert_logic_error(error)

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
        for i in range(error.info[2]):
            def_errors = (x for x in error.child_errors
                          if x.schema_path[-2] == i)
            for child_error in def_errors:
                field = child_error.document_path[-1]
                path = child_error.document_path[:-1] + \
                    ('definition % s' % i, field)
                self.insert_error(path, self.format_message(field, child_error))  # noqa


# TODO docs
# TODO add an ErrorTreeHandler (a dict with raw and verbose error-information)
# TODO add a SerializeErrorHandler (xml, json, yaml)
# TODO add a HumanErrorHandler supporting l10n
