import re
import typing
from ast import literal_eval
from collections import abc, ChainMap
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    ClassVar,
    Container,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Sized,
    Tuple,
    Type,
    Union,
)
from warnings import warn

from cerberus import errors
from cerberus.platform import get_type_args, get_type_origin, ForwardRef, _GenericAlias
from cerberus.typing import (
    AllowUnknown,
    Document,
    DocumentPath,
    ErrorHandlerConfig,
    FieldName,
    NoneType,
    RegistryItem,
    RegistryItems,
    RulesSet,
    Schema,
    TypesMapping,
)
from cerberus.utils import drop_item_from_tuple, readonly_classproperty, schema_hash

RULE_SCHEMA_SEPARATOR = "The rule's arguments are validated against this schema:"
toy_error_handler = errors.ToyErrorHandler()


_ellipsis = typing.Tuple[int, ...].__args__[-1]


def dummy_for_rule_validation(rule_constraints: str) -> Callable:
    def dummy(self, constraint, field, value):
        raise RuntimeError(
            'Dummy method called. Its purpose is to hold just'
            'validation constraints for a rule in its '
            'docstring.'
        )

    f = dummy
    f.__doc__ = rule_constraints
    return f


# Exceptions


class DocumentError(Exception):
    """ Raised when the target document is missing or has the wrong format """


class SchemaError(Exception):
    """ Raised when the validation schema is missing, has the wrong format or
        contains errors. """


# Schema mangling


_normalized_rulesset_cache = {}  # type: Dict[int, Dict[str, Any]]


def normalize_rulesset(rules: RulesSet) -> RulesSet:
    """ Transforms a set of rules into a canonical form. """
    if not isinstance(rules, abc.Mapping):
        return rules

    _hash = schema_hash(rules)
    if _hash in _normalized_rulesset_cache:
        return _normalized_rulesset_cache[_hash]

    rules = dict(rules)

    rules_with_whitespace = [x for x in rules if " " in x]
    if rules_with_whitespace:
        for rule in rules_with_whitespace:
            rules[rule.replace(" ", "_")] = rules.pop(rule)

    if isinstance(rules.get("dependencies"), str):
        rules["dependencies"] = (rules["dependencies"],)

    if "excludes" in rules:
        constraint = rules["excludes"]
        if isinstance(constraint, str) or not isinstance(constraint, Container):
            rules["excludes"] = (constraint,)

    if "type" in rules:
        constraint = rules["type"]
        if not (isinstance(constraint, Iterable) and not isinstance(constraint, str)):
            rules["type"] = (constraint,)

        _expand_generic_type_aliases(rules)

    _expand_composed_of_rules(rules)
    _normalize_contained_rulessets(rules)
    _normalized_rulesset_cache[_hash] = rules
    return rules


def normalize_schema(schema: Schema) -> Schema:
    """ Transforms a schema into a canonical form. """
    return {field: normalize_rulesset(rules) for field, rules in schema.items()}


def _expand_generic_type_aliases(rules: Dict[str, Any]) -> None:
    compound_types = []
    plain_types = []
    is_nullable = False

    for constraint in _flatten_Union_and_Optional(rules.pop("type")):

        if isinstance(constraint, _GenericAlias):

            origin = get_type_origin(constraint)
            args = get_type_args(constraint)

            # mappings, e.g. Mapping[int, str]
            if issubclass(origin, abc.Mapping) and not constraint.__parameters__:
                compound_types.append(
                    {
                        "type": origin,
                        "keysrules": {"type": args[0]},
                        "valuesrules": {"type": args[1]},
                    }
                )

            # list-like and sets, e.g. List[str]
            elif (
                issubclass(origin, (abc.MutableSequence, abc.Set))
                and not constraint.__parameters__
            ):
                compound_types.append({"type": origin, "itemsrules": {"type": args[0]}})

            # tuples
            elif issubclass(origin, tuple) and args:
                # e.g. Tuple[str, ...]
                if args[-1] is _ellipsis:
                    compound_types.append(
                        {"type": origin, "itemsrules": {"type": args[0]}}
                    )
                # e.g. Tuple[int, str, Tuple]
                else:
                    compound_types.append(
                        {"type": origin, "items": tuple({"type": x} for x in args)}
                    )

            else:
                plain_types.append(origin)

        # from typing.Optional
        elif constraint is NoneType:  # type: ignore
            is_nullable = True

        elif isinstance(constraint, ForwardRef):
            plain_types.append(constraint.__forward_arg__)

        else:
            plain_types.append(constraint)

    if compound_types or is_nullable:
        if "anyof" in rules:
            raise SchemaError(
                "The usage of the `anyof` rule is not possible in a rulesset where the"
                "`type` rule specifies compound types as constraints."
            )

        if plain_types:
            compound_types.append({"type": tuple(plain_types)})
        if is_nullable:
            compound_types.append({"nullable": True})

        rules["anyof"] = tuple(compound_types)

    else:
        rules["type"] = tuple(plain_types)


def _flatten_Union_and_Optional(type_constraints):
    for constraint in type_constraints:
        if get_type_origin(constraint) is typing.Union:
            yield from _flatten_Union_and_Optional(get_type_args(constraint))
        else:
            yield constraint


def _expand_composed_of_rules(rules: Dict[str, Any]) -> None:
    """ Expands of-rules that have another rule agglutinated in a rules set. """
    composed_rules = [
        x for x in rules if x.startswith(('allof_', 'anyof_', 'noneof_', 'oneof_'))
    ]
    if not composed_rules:
        return

    for composed_rule in composed_rules:
        of_rule, rule = composed_rule.split('_', 1)
        rules[of_rule] = tuple({rule: x} for x in rules[composed_rule])

    for rule in composed_rules:
        rules.pop(rule)


def _normalize_contained_rulessets(rules: Dict[str, Any]) -> None:
    if isinstance(rules.get("schema"), abc.Mapping):
        rules['schema'] = normalize_schema(rules['schema'])

    for rule in ("allow_unknown", "itemsrules", "keysrules", "valuesrules"):
        if rule in rules:
            rules[rule] = normalize_rulesset(rules[rule])

    for rule in ('allof', 'anyof', 'items', 'noneof', 'oneof'):
        if not isinstance(rules.get(rule), Sequence):
            continue
        rules[rule] = tuple(normalize_rulesset(x) for x in rules[rule])


# Registries


class Registry(Generic[RegistryItem]):
    """ A registry to store and retrieve schemas and parts of it by a name
    that can be used in validation schemas.

    :param definitions: Optional, initial definitions.
    """

    def __init__(
        self, definitions: Union[RegistryItems, Iterable[Tuple[str, RegistryItem]]] = ()
    ):
        self._storage = {}  # type: Dict[str, RegistryItem]
        self.extend(definitions)

    def add(self, name: str, definition: RegistryItem) -> None:
        """ Register a definition to the registry. Existing definitions are
        replaced silently.

        :param name: The name which can be used as reference in a validation
                     schema.
        :param definition: The definition.
        """
        if not isinstance(definition, abc.Mapping):
            raise TypeError("Value must be of Mapping type.")
        # TODO add `_normalize_value: staticmethod` as class attribute declaration when
        # Python3.5 was dropped and remove this # type: ignore
        self._storage[name] = self._normalize_value(definition)  # type: ignore

    def all(self) -> RegistryItems:
        """ Returns a :class:`dict` with all registered definitions mapped to
        their name. """
        return self._storage

    def clear(self):
        """ Purge all definitions in the registry. """
        self._storage.clear()

    def extend(
        self, definitions: Union[RegistryItems, Iterable[Tuple[str, RegistryItem]]]
    ) -> None:
        """ Add several definitions at once. Existing definitions are
        replaced silently.

        :param definitions: The names and definitions.
        """
        for name, definition in dict(definitions).items():
            self.add(name, definition)

    def get(
        self, name: str, default: Optional[RegistryItem] = None
    ) -> Optional[RegistryItem]:
        """ Retrieve a definition from the registry.

        :param name: The reference that points to the definition.
        :param default: Return value if the reference isn't registered. """
        return self._storage.get(name, default)

    def remove(self, *names: str) -> None:
        """ Unregister definitions from the registry.

        :param names: The names of the definitions that are to be
                      unregistered. """
        for name in names:
            self._storage.pop(name, None)


class SchemaRegistry(Registry):
    _normalize_value = staticmethod(normalize_schema)


class RulesSetRegistry(Registry):
    _normalize_value = staticmethod(normalize_rulesset)


schema_registry, rules_set_registry = SchemaRegistry(), RulesSetRegistry()


# Defining types


TypeDefinition = NamedTuple(
    'TypeDefinition',
    (
        ('name', str),
        ('included_types', Tuple[Type[Any], ...]),
        ('excluded_types', Tuple[Type[Any], ...]),
    ),
)
"""
This class is used to define types that can be used as value in the
:attr:`~cerberus.Validator.types_mapping` property.
The ``name`` should be descriptive and match the key it is going to be assigned
to.
A value that is validated against such definition must be an instance of any of
the types contained in ``included_types`` and must not match any of the types
contained in ``excluded_types``.
"""


# The Validator


class ValidatorMeta(type):
    """ Metaclass for all validators """

    def __new__(mcls, name, bases, namespace):
        if '__doc__' not in namespace:
            namespace['__doc__'] = bases[0].__doc__
        return super().__new__(mcls, name, bases, namespace)

    def __init__(cls, name, bases, namespace):
        def attributes_with_prefix(prefix):
            return tuple(
                x[len(prefix) + 2 :]
                for x in dir(cls)
                if x.startswith('_' + prefix + '_')
            )

        super().__init__(name, bases, namespace)

        validation_rules = {
            attribute: cls.__get_rule_schema('_validate_' + attribute)
            for attribute in attributes_with_prefix('validate')
        }

        cls.checkers = tuple(x for x in attributes_with_prefix('check_with'))
        x = validation_rules['check_with']['oneof']
        x[1]['itemsrules']['oneof'][1]['allowed'] = x[2]['allowed'] = cls.checkers

        for rule in (x for x in cls.mandatory_validations if x != 'nullable'):
            validation_rules[rule]['required'] = True

        cls.coercers, cls.default_setters, normalization_rules = (), (), {}
        for attribute in attributes_with_prefix('normalize'):
            if attribute.startswith('coerce_'):
                cls.coercers += (attribute[len('coerce_') :],)
            elif attribute.startswith('default_setter_'):
                cls.default_setters += (attribute[len('default_setter_') :],)
            else:
                normalization_rules[attribute] = cls.__get_rule_schema(
                    '_normalize_' + attribute
                )

        for rule in ('coerce', 'rename_handler'):
            x = normalization_rules[rule]['oneof']
            x[1]['itemsrules']['oneof'][1]['allowed'] = x[2]['allowed'] = cls.coercers
        normalization_rules['default_setter']['oneof'][1][
            'allowed'
        ] = cls.default_setters

        cls.normalization_rules = normalize_schema(normalization_rules)
        cls.validation_rules = normalize_schema(validation_rules)
        cls.rules = ChainMap(cls.normalization_rules, cls.validation_rules)

    def __get_rule_schema(mcls, method_name):
        docstring = getattr(mcls, method_name).__doc__
        if docstring is None:
            result = {}
        else:
            if RULE_SCHEMA_SEPARATOR in docstring:
                docstring = docstring.split(RULE_SCHEMA_SEPARATOR)[1]
            try:
                result = literal_eval(docstring.strip())
            except Exception:
                result = {}

        if not result and method_name != '_validate_meta':
            warn(
                "No validation schema is defined for the arguments of rule "
                "'%s'" % method_name.split('_', 2)[-1]
            )

        return result


class UnconcernedValidator(metaclass=ValidatorMeta):
    """ Validator class. Normalizes and/or validates any mapping against a
    validation-schema which is provided as an argument at class instantiation
    or upon calling the :meth:`~cerberus.Validator.validate`,
    :meth:`~cerberus.Validator.validated` or
    :meth:`~cerberus.Validator.normalized` method. An instance itself is
    callable and executes a validation.

    All instantiation parameters are optional.

    There are the introspective properties :attr:`types`, :attr:`validators`,
    :attr:`coercers`, :attr:`default_setters`, :attr:`rules`,
    :attr:`normalization_rules` and :attr:`validation_rules`.

    The attributes reflecting the available rules are assembled considering
    constraints that are defined in the docstrings of rules' methods and is
    effectively used as validation schema for :attr:`schema`.

    :param schema: See :attr:`~cerberus.Validator.schema`.
                   Defaults to :obj:`None`.
    :param ignore_none_values: See :attr:`~cerberus.Validator.ignore_none_values`.
                               Defaults to ``False``.
    :param allow_unknown: See :attr:`~cerberus.Validator.allow_unknown`.
                          Defaults to ``False``.
    :param require_all: See :attr:`~cerberus.Validator.require_all`.
                        Defaults to ``False``.
    :param purge_unknown: See :attr:`~cerberus.Validator.purge_unknown`.
                          Defaults to to ``False``.
    :param purge_readonly: Removes all fields that are defined as ``readonly`` in the
                           normalization phase.
    :param error_handler: The error handler that formats the result of
                          :attr:`~cerberus.Validator.errors`.
                          When given as two-value tuple with an error-handler
                          class and a dictionary, the latter is passed to the
                          initialization of the error handler.
                          Default: :class:`~cerberus.errors.BasicErrorHandler`.
    """

    mandatory_validations = ('nullable',)  # type: ClassVar[Tuple[str, ...]]
    """ Rules that are evaluated on any field, regardless whether defined in
        the schema or not."""
    priority_validations = (
        'nullable',
        'readonly',
        'type',
        'empty',
    )  # type: ClassVar[Tuple[str, ...]]
    """ Rules that will be processed in that order before any other. """
    types_mapping = {
        'boolean': TypeDefinition('boolean', (bool,), ()),
        'bytearray': TypeDefinition('bytearray', (bytearray,), ()),
        'bytes': TypeDefinition('bytes', (bytes,), ()),
        'complex': TypeDefinition('complex', (complex,), ()),
        'date': TypeDefinition('date', (date,), (datetime,)),
        'datetime': TypeDefinition('datetime', (datetime,), ()),
        'dict': TypeDefinition('dict', (Mapping,), ()),
        'float': TypeDefinition('float', (float,), ()),
        'frozenset': TypeDefinition('frozenset', (frozenset,), ()),
        'integer': TypeDefinition('integer', (int,), (bool,)),
        'list': TypeDefinition('list', (list,), ()),
        'number': TypeDefinition('number', (int, float), (bool,)),
        'set': TypeDefinition('set', (set,), ()),
        'string': TypeDefinition('string', (str,), ()),
        'tuple': TypeDefinition('tuple', (tuple,), ()),
        'type': TypeDefinition('type', (type,), ()),
    }  # type: ClassVar[TypesMapping]
    """ This mapping holds all available constraints for the type rule and
        their assigned :class:`~cerberus.TypeDefinition`. """
    types_mapping.update(
        (x, TypeDefinition(x, (getattr(abc, x),), ()))
        for x in abc.__all__  # type: ignore
    )

    _valid_schemas = set()  # type: ClassVar[Set[Tuple[int, int]]]
    """ A :class:`set` of hashes derived from validation schemas that are
        legit for a particular ``Validator`` class. """

    # these will be set by the metaclass, here type hints are given:
    checkers = ()  # type: ClassVar[Tuple[str, ...]]
    coercers = ()  # type: ClassVar[Tuple[str, ...]]
    default_setters = ()  # type: ClassVar[Tuple[str, ...]]
    normalization_rules = {}  # type: ClassVar[Schema]
    rules = {}  # type: ClassVar[Dict[str, RulesSet]]
    validation_rules = {}  # type: ClassVar[Schema]

    def __init__(
        self,
        schema: Schema = None,
        *,
        allow_unknown: AllowUnknown = False,
        error_handler: ErrorHandlerConfig = errors.BasicErrorHandler,
        ignore_none_values: bool = False,
        purge_unknown: bool = False,
        purge_readonly: bool = False,
        require_all: bool = False,
        rules_set_registry: RulesSetRegistry = rules_set_registry,
        schema_registry: SchemaRegistry = schema_registry,
        **extra_config: Any
    ):
        self._config = extra_config  # type: Dict[str, Any]
        """ This dictionary holds the configuration arguments that were used to
            initialize the :class:`Validator` instance except the ``error_handler``. """
        self._config.update(
            {
                "error_handler": error_handler,
                "ignore_none_values": ignore_none_values,
                "purge_readonly": purge_readonly,
                "purge_unknown": purge_unknown,
                "require_all": require_all,
                "rules_set_registry": rules_set_registry,
                "schema_registry": schema_registry,
            }
        )

        self.document = None  # type: Optional[Document]
        """ The document that is or was recently processed.
            Type: any :term:`mapping` """
        self._errors = errors.ErrorList()
        """ The list of errors that were encountered since the last document
            processing was invoked.
            Type: :class:`~cerberus.errors.ErrorList` """
        self.recent_error = None  # type: Optional[errors.ValidationError]
        """ The last individual error that was submitted.
            Type: :class:`~cerberus.errors.ValidationError` or ``None`` """
        self.document_error_tree = errors.DocumentErrorTree()
        """ A tree representiation of encountered errors following the
            structure of the document.
            Type: :class:`~cerberus.errors.DocumentErrorTree` """
        self.schema_error_tree = errors.SchemaErrorTree()
        """ A tree representiation of encountered errors following the
            structure of the schema.
            Type: :class:`~cerberus.errors.SchemaErrorTree` """
        self.document_path = ()  # type: DocumentPath
        """ The path within the document to the current sub-document.
            Type: :class:`tuple` """
        self.schema_path = ()  # type: DocumentPath
        """ The path within the schema to the current sub-schema.
            Type: :class:`tuple` """
        self.update = False
        self.error_handler = self.__init_error_handler(error_handler)
        """ The error handler used to format :attr:`~cerberus.Validator.errors`
            and process submitted errors with
            :meth:`~cerberus.Validator._error`.
            Type: :class:`~cerberus.errors.BaseErrorHandler` """
        self.schema = schema
        self.allow_unknown = allow_unknown
        self._remaining_rules = []  # type: List[str]
        """ Keeps track of the rules that are next in line to be evaluated during the
            validation of a field. Type: :class:`list` """

        super().__init__()

    @staticmethod
    def __init_error_handler(config: ErrorHandlerConfig) -> errors.BaseErrorHandler:
        if isinstance(config, errors.BaseErrorHandler):
            return config

        if isinstance(config, tuple):
            error_handler, eh_config = config

        else:
            error_handler, eh_config = config, {}

        if isinstance(error_handler, type) and issubclass(
            error_handler, errors.BaseErrorHandler
        ):
            return error_handler(**eh_config)

        else:
            raise RuntimeError('Invalid error_handler configuration.')

    @classmethod
    def clear_caches(cls):
        """ Purge the cache of known valid schemas. """
        cls._valid_schemas.clear()

    def _error(self, *args):
        """ Creates and adds one or multiple errors.

        :param args: Accepts different argument's signatures.

                     *1. Bulk addition of errors:*

                     - :term:`iterable` of
                       :class:`~cerberus.errors.ValidationError`-instances

                     The errors will be added to
                     :attr:`~cerberus.Validator._errors`.

                     *2. Custom error:*

                     - the invalid field's name

                     - the error message

                     A custom error containing the message will be created and
                     added to :attr:`~cerberus.Validator._errors`.
                     There will however be fewer information contained in the
                     error (no reference to the violated rule and its
                     constraint).

                     *3. Defined error:*

                     - the invalid field's name

                     - the error-reference, see :mod:`cerberus.errors`

                     - arbitrary, supplemental information about the error

                     A :class:`~cerberus.errors.ValidationError` instance will
                     be created and added to
                     :attr:`~cerberus.Validator._errors`.
        """
        if len(args) == 1:
            self._errors.extend(args[0])
            for error in args[0]:
                self.document_error_tree.add(error)
                self.schema_error_tree.add(error)
                self.error_handler.emit(error)
        elif len(args) == 2 and isinstance(args[1], str):
            self._error(args[0], errors.CUSTOM, args[1])
        elif len(args) >= 2:
            field = args[0]
            code = args[1].code
            rule = args[1].rule
            info = args[2:]

            document_path = self.document_path + (field,)

            schema_path = self.schema_path
            if code != errors.UNKNOWN_FIELD.code and rule is not None:
                schema_path += (field, rule)

            if not rule:
                constraint = None
            else:
                field_definitions = self._resolve_rules_set(self.schema[field])
                if rule == 'nullable':
                    constraint = field_definitions.get(rule, False)
                elif rule == 'required':
                    constraint = field_definitions.get(rule, self.require_all)
                    if rule not in field_definitions:
                        schema_path = "__require_all__"
                else:
                    constraint = field_definitions[rule]

            value = self.document.get(field)

            self.recent_error = errors.ValidationError(
                document_path, schema_path, code, rule, constraint, value, info
            )
            self._error([self.recent_error])

    def _get_child_validator(
        self,
        document_crumb: Union[FieldName, Iterable[FieldName], None] = None,
        schema_crumb: Union[FieldName, Iterable[FieldName], None] = None,
        **kwargs: Any
    ) -> 'UnconcernedValidator':
        """ Creates a new instance of Validator-(sub-)class. All initial parameters of
            the parent are passed to the initialization, unless a parameter is given as
            an explicit *keyword*-parameter.
        :param document_crumb: Extends the :attr:`~cerberus.Validator.document_path`
                               of the child-validator.
        :param schema_crumb: Extends the :attr:`~cerberus.Validator.schema_path`
                             of the child-validator.
        :param kwargs: Overriding keyword-arguments for initialization.
        """
        child_config = ChainMap(kwargs, self._config)
        if not self.is_child:
            child_config = child_config.new_child(
                {
                    'is_child': True,
                    'error_handler': toy_error_handler,
                    'root_allow_unknown': self.allow_unknown,
                    'root_document': self.document,
                    'root_schema': self.schema,
                }
            )
        child_validator = self.__class__(**child_config)

        if document_crumb is None:
            child_validator.document_path = self.document_path
        else:
            if not isinstance(document_crumb, tuple):
                document_crumb = (document_crumb,)
            child_validator.document_path = self.document_path + document_crumb

        if schema_crumb is None:
            child_validator.schema_path = self.schema_path
        else:
            if not isinstance(schema_crumb, tuple):
                schema_crumb = (schema_crumb,)
            child_validator.schema_path = self.schema_path + schema_crumb

        return child_validator

    def __get_rule_handler(self, domain, rule):
        methodname = '_{0}_{1}'.format(domain, rule.replace(' ', '_'))
        result = getattr(self, methodname, None)
        if result is None:
            raise RuntimeError(
                "There's no handler for '{}' in the '{}' "
                "domain.".format(rule, domain)
            )
        return result

    def _drop_nodes_from_errorpaths(
        self,
        _errors: errors.ErrorList,
        dp_items: Iterable[int],
        sp_items: Iterable[int],
    ) -> None:
        """ Removes nodes by index from an errorpath, relatively to the
            basepaths of self.

        :param errors: A list of :class:`errors.ValidationError` instances.
        :param dp_items: A list of integers, pointing at the nodes to drop from
                         the :attr:`document_path`.
        :param sp_items: Alike ``dp_items``, but for :attr:`schema_path`.
        """
        dp_basedepth = len(self.document_path)
        sp_basedepth = len(self.schema_path)
        for error in _errors:
            for i in sorted(dp_items, reverse=True):
                error.document_path = drop_item_from_tuple(
                    error.document_path, dp_basedepth + i
                )
            for i in sorted(sp_items, reverse=True):
                error.schema_path = drop_item_from_tuple(
                    error.schema_path, sp_basedepth + i
                )
            if error.child_errors:
                self._drop_nodes_from_errorpaths(error.child_errors, dp_items, sp_items)

    def _lookup_field(self, path):
        """ Searches for a field as defined by path. This method is used by the
            ``dependency`` evaluation logic.

        :param path: Path elements are separated by a ``.``. A leading ``^``
                     indicates that the path relates to the document root,
                     otherwise it relates to the currently evaluated document,
                     which is possibly a subdocument.
                     The sequence ``^^`` at the start will be interpreted as a
                     literal ``^``.
        :type path: :class:`str`
        :returns: Either the found field name and its value or :obj:`None` for
                  both.
        :rtype: A two-value :class:`tuple`.
        """
        if path.startswith('^'):
            path = path[1:]
            context = self.document if path.startswith('^') else self.root_document
        else:
            context = self.document

        parts = path.split('.')
        for part in parts:
            if part not in context:
                return None, None
            context = context.get(part, {})

        return parts[-1], context

    def _resolve_rules_set(self, rules_set):
        if isinstance(rules_set, Mapping):
            return rules_set
        elif isinstance(rules_set, str):
            return self.rules_set_registry.get(rules_set)
        return None

    def _resolve_schema(self, schema):
        if isinstance(schema, Mapping):
            return schema
        elif isinstance(schema, str):
            return self.schema_registry.get(schema)
        return None

    # Properties
    # TODO replace a lot with __getattr__ and __setattr__

    @property
    def allow_unknown(self) -> AllowUnknown:
        """ If ``True`` unknown fields that are not defined in the schema will
            be ignored. If a mapping with a validation schema is given, any
            undefined field will be validated against its rules.
            Also see :ref:`allowing-the-unknown`.
            Type: :class:`bool` or any :term:`mapping` """
        return self._config.get('allow_unknown', False)

    @allow_unknown.setter
    def allow_unknown(self, value: AllowUnknown) -> None:
        if isinstance(value, Mapping):
            self._config['allow_unknown'] = normalize_rulesset(value)
        elif isinstance(value, bool):
            self._config['allow_unknown'] = value
        else:
            raise TypeError

    @property
    def errors(self) -> Any:
        """ The errors of the last processing formatted by the handler that is
            bound to :attr:`~cerberus.Validator.error_handler`. """
        return self.error_handler(self._errors)

    @property
    def ignore_none_values(self) -> bool:
        """ Whether to not process :obj:`None`-values in a document or not.
            Type: :class:`bool` """
        return self._config.get('ignore_none_values', False)

    @ignore_none_values.setter
    def ignore_none_values(self, value: bool) -> None:
        self._config['ignore_none_values'] = value

    @property
    def is_child(self) -> bool:
        """ ``True`` for child-validators obtained with
        :meth:`~cerberus.Validator._get_child_validator`.
        Type: :class:`bool` """
        return self._config.get('is_child', False)

    @property
    def _is_normalized(self) -> bool:
        """ ``True`` if the document is already normalized. """
        return self._config.get('_is_normalized', False)

    @_is_normalized.setter
    def _is_normalized(self, value: bool) -> None:
        self._config['_is_normalized'] = value

    @property
    def purge_unknown(self) -> bool:
        """ If ``True``, unknown fields will be deleted from the document
            unless a validation is called with disabled normalization.
            Also see :ref:`purging-unknown-fields`. Type: :class:`bool` """
        return self._config.get('purge_unknown', False)

    @purge_unknown.setter
    def purge_unknown(self, value: bool) -> None:
        self._config['purge_unknown'] = value

    @property
    def purge_readonly(self) -> bool:
        """ If ``True``, fields declared as readonly will be deleted from the
            document unless a validation is called with disabled normalization.
            Type: :class:`bool` """
        return self._config.get('purge_readonly', False)

    @purge_readonly.setter
    def purge_readonly(self, value: bool) -> None:
        self._config['purge_readonly'] = value

    @property
    def require_all(self) -> bool:
        """ If ``True`` known fields that are defined in the schema will
            be required. Type: :class:`bool` """
        return self._config["require_all"]

    @require_all.setter
    def require_all(self, value: bool) -> None:
        self._config['require_all'] = value

    @property
    def root_allow_unknown(self) -> AllowUnknown:
        """ The :attr:`~cerberus.Validator.allow_unknown` attribute of the
            first level ancestor of a child validator. """
        return self._config.get('root_allow_unknown', self.allow_unknown)

    @property
    def root_require_all(self) -> bool:
        """ The :attr:`~cerberus.Validator.require_all` attribute of
            the first level ancestor of a child validator. """
        return self._config.get('root_require_all', self.require_all)

    @property
    def root_document(self) -> Document:
        """ The :attr:`~cerberus.Validator.document` attribute of the
            first level ancestor of a child validator. """
        return self._config.get('root_document', self.document)

    @property
    def rules_set_registry(self) -> RulesSetRegistry:
        """ The registry that holds referenced rules sets.
            Type: :class:`~cerberus.Registry` """
        return self._config["rules_set_registry"]

    @rules_set_registry.setter
    def rules_set_registry(self, registry: RulesSetRegistry) -> None:
        self._config['rules_set_registry'] = registry

    @property
    def root_schema(self) -> Optional[Schema]:
        """ The :attr:`~cerberus.Validator.schema` attribute of the
            first level ancestor of a child validator. """
        return self._config.get('root_schema', self.schema)

    @property  # type: ignore
    def schema(self):
        """ The validation schema of a validator. When a schema is passed to
            a validator method (e.g. ``validate``), it replaces this attribute.
            Type: any :term:`mapping` or :obj:`None` """
        return self._schema

    @schema.setter
    def schema(self, schema):
        if schema is None:
            self._schema = None
        elif self.is_child:
            self._schema = schema
        else:
            self._schema = normalize_schema(schema)

    @property
    def schema_registry(self) -> SchemaRegistry:
        """ The registry that holds referenced schemas.
            Type: :class:`~cerberus.Registry` """
        return self._config["schema_registry"]

    @schema_registry.setter
    def schema_registry(self, registry: SchemaRegistry) -> None:
        self._config['schema_registry'] = registry

    # FIXME the returned method has the correct docstring, but doesn't appear
    #       in the API docs
    @readonly_classproperty
    def types(cls) -> Tuple[str, ...]:
        """ The constraints that can be used for the 'type' rule.
            Type: A tuple of strings. """
        return tuple(cls.types_mapping)

    # Document processing

    def __init_processing(self, document, schema=None):
        self._errors = errors.ErrorList()
        self.recent_error = None
        self.document_error_tree = errors.DocumentErrorTree()
        self.schema_error_tree = errors.SchemaErrorTree()
        if not self.is_child:
            self._is_normalized = False

        if schema is not None:
            self.schema = schema

        if self.schema is None:
            if isinstance(self.allow_unknown, Mapping):
                self.schema = {}
            else:
                raise SchemaError(errors.MISSING_SCHEMA)

        if document is None:
            raise DocumentError(errors.DOCUMENT_MISSING)
        if not isinstance(document, Mapping):
            raise DocumentError(errors.DOCUMENT_FORMAT.format(document))
        self.document = document
        self.error_handler.start(self)

    def _drop_remaining_rules(self, *rules):
        """ Drops rules from the queue of the rules that still need to be
            evaluated for the currently processed field.
            If no arguments are given, the whole queue is emptied.
        """
        if rules:
            for rule in (x for x in rules if x in self._remaining_rules):
                self._remaining_rules.remove(rule)
        else:
            self._remaining_rules.clear()

    # # Normalizing

    def normalized(
        self,
        document: Document,
        schema: Optional[Schema] = None,
        always_return_document: bool = False,
    ) -> Optional[Document]:
        """
        Returns the document normalized according to the specified rules of a schema.

        :param document: The document to normalize.
        :param schema: The validation schema. Defaults to :obj:`None`. If not
                       provided here, the schema must have been provided at
                       class instantiation.
        :param always_return_document: Return the document, even if an error
                                       occurred. Defaults to: ``False``.
        :return: A normalized copy of the provided mapping or :obj:`None` if an
                 error occurred during normalization.
        """
        self.__init_processing(document, schema)
        self.document = self.__normalize_mapping(document, self.schema)
        self.error_handler.end(self)
        self._errors.sort()
        if self._errors and not always_return_document:
            return None
        else:
            return self.document

    def __normalize_mapping(self, mapping, schema):
        mapping = mapping.copy()

        if isinstance(schema, str):
            schema = self._resolve_schema(schema)
        schema = {k: self._resolve_rules_set(v) for k, v in schema.items()}

        self.__normalize_rename_fields(mapping, schema)
        if self.purge_unknown and not self.allow_unknown:
            self._normalize_purge_unknown(mapping, schema)
        if self.purge_readonly:
            self.__normalize_purge_readonly(mapping, schema)
        # Check `readonly` fields before applying default values because
        # a field's schema definition might contain both `readonly` and
        # `default`.
        self.__validate_readonly_fields(mapping, schema)
        self.__normalize_default_fields(mapping, schema)
        self._normalize_coerce(mapping, schema)
        self.__normalize_containers(mapping, schema)
        self._is_normalized = True
        return mapping

    def _normalize_coerce(self, mapping, schema):
        """ {'oneof': [
                {'type': 'Callable'},
                {'type': 'Iterable',
                 'itemsrules': {'oneof': [{'type': 'Callable'},
                                          {'type': 'string'}]}},
                {'type': 'string'}
                ]} """

        error = errors.COERCION_FAILED
        for field in mapping:
            if field in schema and 'coerce' in schema[field]:
                mapping[field] = self.__normalize_coerce(
                    schema[field]['coerce'],
                    field,
                    mapping[field],
                    schema[field].get('nullable', False),
                    error,
                )
            elif (
                isinstance(self.allow_unknown, Mapping)
                and 'coerce' in self.allow_unknown
            ):
                mapping[field] = self.__normalize_coerce(
                    self.allow_unknown['coerce'],
                    field,
                    mapping[field],
                    self.allow_unknown.get('nullable', False),
                    error,
                )

    def __normalize_coerce(self, processor, field, value, nullable, error):
        if isinstance(processor, str):
            processor = self.__get_rule_handler('normalize_coerce', processor)

        elif isinstance(processor, Iterable):
            result = value
            for p in processor:
                result = self.__normalize_coerce(p, field, result, nullable, error)
                if (
                    errors.COERCION_FAILED
                    in self.document_error_tree.fetch_errors_from(
                        self.document_path + (field,)
                    )
                ):
                    break
            return result

        try:
            return processor(value)
        except RuntimeError:
            raise
        except Exception as e:
            if not (nullable and value is None):
                self._error(field, error, str(e))
            return value

    def __normalize_containers(self, mapping, schema):
        for field in mapping:
            rules = set(schema.get(field, ()))

            if isinstance(mapping[field], Mapping):
                if 'keysrules' in rules:
                    self.__normalize_mapping_per_keysrules(
                        field, mapping, schema[field]['keysrules']
                    )
                if 'valuesrules' in rules:
                    self.__normalize_mapping_per_valuesrules(
                        field, mapping, schema[field]['valuesrules']
                    )
                if any(
                    x in rules for x in ('allow_unknown', 'purge_unknown', 'schema')
                ) or isinstance(self.allow_unknown, Mapping):
                    self.__normalize_mapping_per_schema(field, mapping, schema)

            elif isinstance(mapping[field], str):
                continue

            elif isinstance(mapping[field], Sequence):
                if 'itemsrules' in rules:
                    self.__normalize_sequence_per_itemsrules(field, mapping, schema)
                elif 'items' in rules:
                    self.__normalize_sequence_per_items(field, mapping, schema)

    def __normalize_mapping_per_keysrules(self, field, mapping, property_rules):
        schema = {k: property_rules for k in mapping[field]}
        document = {k: k for k in mapping[field]}
        validator = self._get_child_validator(
            document_crumb=field, schema_crumb=(field, 'keysrules'), schema=schema
        )
        result = validator.normalized(document, always_return_document=True)
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2, 4])
            self._error(validator._errors)
        for _in, out in ((k, v) for k, v in result.items() if k != v):
            if out in mapping[field]:
                warn(
                    "Normalizing keys of {path}: {key} already exists, "
                    "its value is replaced.".format(
                        path='.'.join(str(x) for x in self.document_path + (field,)),
                        key=_in,
                    )
                )
                mapping[field][out] = mapping[field][_in]
            else:
                mapping[field][out] = mapping[field][_in]
                del mapping[field][_in]

    def __normalize_mapping_per_valuesrules(self, field, mapping, value_rules):
        schema = {k: value_rules for k in mapping[field]}
        validator = self._get_child_validator(
            document_crumb=field, schema_crumb=(field, 'valuesrules'), schema=schema
        )
        mapping[field] = validator.normalized(
            mapping[field], always_return_document=True
        )
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(validator._errors)

    def __normalize_mapping_per_schema(self, field, mapping, schema):
        rules = schema.get(field, {})
        if not rules and isinstance(self.allow_unknown, Mapping):
            rules = self.allow_unknown
        validator = self._get_child_validator(
            document_crumb=field,
            schema_crumb=(field, 'schema'),
            schema=rules.get('schema', {}),
            allow_unknown=rules.get('allow_unknown', self.allow_unknown),  # noqa: E501
            purge_unknown=rules.get('purge_unknown', self.purge_unknown),
            require_all=rules.get('require_all', self.require_all),
        )  # noqa: E501
        value_type = type(mapping[field])
        result_value = validator.normalized(mapping[field], always_return_document=True)
        mapping[field] = value_type(result_value)
        if validator._errors:
            self._error(validator._errors)

    def __normalize_sequence_per_items(self, field, mapping, schema):
        rules, values = schema[field]['items'], mapping[field]
        if len(rules) != len(values):
            return
        schema = {k: v for k, v in enumerate(rules)}
        document = {k: v for k, v in enumerate(values)}
        validator = self._get_child_validator(
            document_crumb=field, schema_crumb=(field, 'items'), schema=schema
        )
        value_type = type(mapping[field])
        result = validator.normalized(document, always_return_document=True)
        mapping[field] = value_type(result.values())
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(validator._errors)

    def __normalize_sequence_per_itemsrules(self, field, mapping, schema):
        constraint = schema[field]['itemsrules']
        schema = {k: constraint for k in range(len(mapping[field]))}
        document = {k: v for k, v in enumerate(mapping[field])}
        validator = self._get_child_validator(
            document_crumb=field, schema_crumb=(field, 'itemsrules'), schema=schema
        )
        value_type = type(mapping[field])
        result = validator.normalized(document, always_return_document=True)
        mapping[field] = value_type(result.values())
        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(validator._errors)

    @staticmethod
    def __normalize_purge_readonly(mapping, schema):
        for field in [x for x in mapping if schema.get(x, {}).get('readonly', False)]:
            mapping.pop(field)
        return mapping

    @staticmethod
    def _normalize_purge_unknown(mapping, schema):
        """ {'type': 'boolean'} """
        for field in [x for x in mapping if x not in schema]:
            mapping.pop(field)
        return mapping

    def __normalize_rename_fields(self, mapping, schema):
        for field in tuple(mapping):
            if field in schema:
                self._normalize_rename(mapping, schema, field)
                self._normalize_rename_handler(mapping, schema, field)
            elif (
                isinstance(self.allow_unknown, Mapping)
                and 'rename_handler' in self.allow_unknown
            ):
                self._normalize_rename_handler(
                    mapping, {field: self.allow_unknown}, field
                )
        return mapping

    def _normalize_rename(self, mapping, schema, field):
        """ {'type': 'Hashable'} """
        if 'rename' in schema[field]:
            mapping[schema[field]['rename']] = mapping[field]
            del mapping[field]

    def _normalize_rename_handler(self, mapping, schema, field):
        """ {'oneof': [
                {'type': 'Callable'},
                {'type': 'Iterable',
                 'itemsrules': {'oneof': [{'type': 'Callable'},
                                          {'type': 'string'}]}},
                {'type': 'string'}
                ]} """
        if 'rename_handler' not in schema[field]:
            return
        new_name = self.__normalize_coerce(
            schema[field]['rename_handler'], field, field, False, errors.RENAMING_FAILED
        )
        if new_name != field:
            mapping[new_name] = mapping[field]
            del mapping[field]

    def __validate_readonly_fields(self, mapping, schema):
        for field in (
            x
            for x in schema
            if x in mapping and self._resolve_rules_set(schema[x]).get('readonly')
        ):
            self._validate_readonly(schema[field]['readonly'], field, mapping[field])

    def __normalize_default_fields(self, mapping, schema):
        empty_fields = [
            x
            for x in schema
            if x not in mapping
            or (
                mapping[x] is None  # noqa: W503
                and not schema[x].get('nullable', False)
            )  # noqa: W503
        ]

        for field in (x for x in empty_fields if 'default' in schema[x]):
            self._normalize_default(mapping, schema, field)

        known_fields_states = set()
        fields_with_default_setter = [
            x for x in empty_fields if 'default_setter' in schema[x]
        ]
        while fields_with_default_setter:
            field = fields_with_default_setter.pop(0)
            try:
                self._normalize_default_setter(mapping, schema, field)
            except KeyError:
                fields_with_default_setter.append(field)
            except RuntimeError:
                raise
            except Exception as e:
                self._error(field, errors.SETTING_DEFAULT_FAILED, str(e))

            fields_processing_state = hash(tuple(fields_with_default_setter))
            if fields_processing_state in known_fields_states:
                for field in fields_with_default_setter:
                    self._error(
                        field,
                        errors.SETTING_DEFAULT_FAILED,
                        'Circular dependencies of default setters.',
                    )
                break
            else:
                known_fields_states.add(fields_processing_state)

    def _normalize_default(self, mapping, schema, field):
        """ {'nullable': True} """
        mapping[field] = schema[field]['default']

    def _normalize_default_setter(self, mapping, schema, field):
        """ {'oneof': [
                {'type': 'Callable'},
                {'type': 'string'}
                ]} """
        if 'default_setter' in schema[field]:
            setter = schema[field]['default_setter']
            if isinstance(setter, str):
                setter = self.__get_rule_handler('normalize_default_setter', setter)
            mapping[field] = setter(mapping)

    # # Validating

    def validate(
        self,
        document: Document,
        schema: Optional[Schema] = None,
        update: bool = False,
        normalize: bool = True,
    ) -> bool:
        """
        Normalizes and validates a mapping against a validation-schema of defined rules.

        :param document: The document to normalize.
        :param schema: The validation schema. Defaults to :obj:`None`. If not provided
                       here, the schema must have been provided at class instantiation.
        :param update: If ``True``, required fields won't be checked.
        :param normalize: If ``True``, normalize the document before validation.
        :return: ``True`` if validation succeeds, otherwise ``False``. Check
                 the :func:`errors` property for a list of processing errors.
        """
        self.update = update
        self._unrequired_by_excludes = set()  # type: Set[FieldName]

        self.__init_processing(document, schema)
        del document, schema

        if normalize:
            self.document = self.__normalize_mapping(self.document, self.schema)

        for field in self.document:  # type: ignore
            definitions = self.schema.get(field)  # type: ignore
            if definitions is not None:
                self.__validate_definitions(definitions, field)
            else:
                self.__validate_unknown_fields(field)

        if not self.update:
            self.__validate_required_fields(self.document)

        self.error_handler.end(self)
        self._errors.sort()

        return not bool(self._errors)

    __call__ = validate

    def validated(
        self,
        document: Document,
        schema: Optional[Schema] = None,
        update: bool = False,
        normalize: bool = True,
        always_return_document: bool = False,
    ) -> Optional[Document]:
        """
        Wrapper around :meth:`~cerberus.Validator.validate` that returns the normalized
        and validated document or :obj:`None` if validation failed.
        """
        self.validate(
            document=document, schema=schema, update=update, normalize=normalize
        )
        if self._errors and not always_return_document:
            return None
        else:
            return self.document

    def __validate_unknown_fields(self, field):
        if self.allow_unknown:
            value = self.document[field]
            if isinstance(self.allow_unknown, (Mapping, str)):
                # validate that unknown fields matches the schema
                # for unknown_fields
                schema_crumb = 'allow_unknown' if self.is_child else '__allow_unknown__'
                validator = self._get_child_validator(
                    schema_crumb=schema_crumb, schema={field: self.allow_unknown}
                )
                if not validator({field: value}, normalize=False):
                    self._error(validator._errors)
        else:
            self._error(field, errors.UNKNOWN_FIELD)

    def __validate_definitions(self, definitions, field):
        """ Validate a field's value against its defined rules. """

        definitions = self._resolve_rules_set(definitions)
        value = self.document[field]

        rules_queue = [
            x
            for x in self.priority_validations
            if x in definitions or x in self.mandatory_validations
        ]
        rules_queue.extend(
            x for x in self.mandatory_validations if x not in rules_queue
        )
        rules_queue.extend(
            x
            for x in definitions
            if x not in rules_queue
            and x not in self.normalization_rules
            and x not in ('allow_unknown', 'require_all', 'meta', 'required')
        )
        self._remaining_rules = rules_queue

        while self._remaining_rules:
            rule = self._remaining_rules.pop(0)
            rule_handler = self.__get_rule_handler('validate', rule)
            rule_handler(definitions.get(rule, None), field, value)

    # Remember to keep the validation methods below this line
    # sorted alphabetically

    _validate_allow_unknown = dummy_for_rule_validation(
        """ {'oneof': [{'type': 'boolean'},
                       {'type': ['dict', 'string'],
                        'check_with': 'rulesset'}]} """
    )

    def _validate_allowed(self, allowed_values, field, value):
        """ {'type': 'container_but_not_string'} """
        if isinstance(value, Iterable) and not isinstance(value, str):
            unallowed = tuple(x for x in value if x not in allowed_values)
            if unallowed:
                self._error(field, errors.UNALLOWED_VALUES, unallowed)
        else:
            if value not in allowed_values:
                self._error(field, errors.UNALLOWED_VALUE, value)

    def _validate_check_with(self, checks, field, value):
        """ {'oneof': [
                {'type': 'Callable'},
                {'type': 'Iterable',
                 'itemsrules': {'oneof': [{'type': 'Callable'},
                                          {'type': 'string'}]}},
                {'type': 'string'}
                ]}
        """
        if isinstance(checks, str):
            value_checker = self.__get_rule_handler('check_with', checks)
            value_checker(field, value)
        elif isinstance(checks, Iterable):
            for v in checks:
                self._validate_check_with(v, field, value)
        else:
            checks(field, value, self._error)

    def _validate_contains(self, expected_values, field, value):
        """ {'empty': False } """
        if not isinstance(value, Container):
            return

        if not isinstance(expected_values, Iterable) or isinstance(
            expected_values, str
        ):
            expected_values = set((expected_values,))
        else:
            expected_values = set(expected_values)

        missing_values = expected_values - set(value)
        if missing_values:
            self._error(field, errors.MISSING_MEMBERS, missing_values)

    def _validate_dependencies(self, dependencies, field, value):
        """ {'type': ('Hashable', 'Iterable', 'Mapping'),
             'check_with': 'dependencies'} """
        if isinstance(dependencies, str):
            dependencies = (dependencies,)

        if isinstance(dependencies, Sequence):
            self.__validate_dependencies_sequence(dependencies, field)
        elif isinstance(dependencies, Mapping):
            self.__validate_dependencies_mapping(dependencies, field)

        if (
            self.document_error_tree.fetch_node_from(
                self.schema_path + (field, 'dependencies')
            )
            is not None
        ):
            return True

    def __validate_dependencies_mapping(self, dependencies, field):
        validated_dependencies_counter = 0
        error_info = {}
        for dependency_name, dependency_values in dependencies.items():
            if not isinstance(dependency_values, Sequence) or isinstance(
                dependency_values, str
            ):
                dependency_values = [dependency_values]

            wanted_field, wanted_field_value = self._lookup_field(dependency_name)
            if wanted_field_value in dependency_values:
                validated_dependencies_counter += 1
            else:
                error_info.update({dependency_name: wanted_field_value})

        if validated_dependencies_counter != len(dependencies):
            self._error(field, errors.DEPENDENCIES_FIELD_VALUE, error_info)

    def __validate_dependencies_sequence(self, dependencies, field):
        for dependency in dependencies:
            if self._lookup_field(dependency)[0] is None:
                self._error(field, errors.DEPENDENCIES_FIELD, dependency)

    def _validate_empty(self, empty, field, value):
        """ {'type': 'boolean'} """
        if isinstance(value, Sized) and len(value) == 0:
            self._drop_remaining_rules(
                'allowed',
                'forbidden',
                'items',
                'minlength',
                'maxlength',
                'regex',
                'check_with',
            )
            if not empty:
                self._error(field, errors.EMPTY)

    def _validate_excludes(self, excluded_fields, field, value):
        """ {'type': ('Hashable', 'Iterable'),
             'itemsrules': {'type': 'Hashable'}} """

        if isinstance(excluded_fields, str) or not isinstance(
            excluded_fields, Container
        ):
            excluded_fields = (excluded_fields,)

        # Mark the currently evaluated field as not required for now if it actually is.
        # One of the so marked will be needed to pass when required fields are checked.
        if self.schema[field].get('required', self.require_all):
            self._unrequired_by_excludes.add(field)

        for excluded_field in excluded_fields:
            if excluded_field in self.schema and self.schema[field].get(
                'required', self.require_all
            ):

                self._unrequired_by_excludes.add(excluded_field)

        if any(excluded_field in self.document for excluded_field in excluded_fields):
            exclusion_str = ', '.join(
                "'{0}'".format(field) for field in excluded_fields
            )
            self._error(field, errors.EXCLUDES_FIELD, exclusion_str)

    def _validate_forbidden(self, forbidden_values, field, value):
        """ {'type': 'Container'} """
        if isinstance(value, str):
            if value in forbidden_values:
                self._error(field, errors.FORBIDDEN_VALUE, value)
        elif isinstance(value, Iterable):
            forbidden = set(value) & set(forbidden_values)
            if forbidden:
                self._error(field, errors.FORBIDDEN_VALUES, list(forbidden))
        else:
            if value in forbidden_values:
                self._error(field, errors.FORBIDDEN_VALUE, value)

    def _validate_items(self, items, field, values):
        """ {'type': 'Sequence', 'check_with': 'items'} """
        if len(items) != len(values):
            self._error(field, errors.ITEMS_LENGTH, len(items), len(values))
        else:
            schema = {i: definition for i, definition in enumerate(items)}

            validator = self._get_child_validator(
                document_crumb=field,
                schema_crumb=(field, 'items'),  # noqa: E501
                schema=schema,
            )
            if not validator(
                {i: value for i, value in enumerate(values)},
                update=self.update,
                normalize=False,
            ):
                self._error(field, errors.ITEMS, validator._errors)

    def _validate_itemsrules(self, rulesset, field, value):
        """ {'type': ('dict', 'string'),
             'check_with': 'rulesset'} """

        if not isinstance(value, Sequence):
            return

        schema = {i: rulesset for i in range(len(value))}
        validator = self._get_child_validator(
            document_crumb=field,
            schema_crumb=(field, 'itemsrules'),
            schema=schema,
            allow_unknown=self.allow_unknown,
        )
        validator(
            {i: v for i, v in enumerate(value)}, update=self.update, normalize=False
        )

        if validator._errors:
            self._drop_nodes_from_errorpaths(validator._errors, [], [2])
            self._error(field, errors.ITEMSRULES, validator._errors)

    def __validate_logical(self, operator, definitions, field, value):
        """ Validates value against all definitions and logs errors according
            to the operator. """
        valid_counter = 0
        _errors = errors.ErrorList()

        for i, definition in enumerate(definitions):
            schema = {field: definition.copy()}
            for rule in ('allow_unknown', 'type'):
                if rule not in definition and rule in self.schema[field]:
                    schema[field][rule] = self.schema[field][rule]
            if 'allow_unknown' not in definition:
                schema[field]['allow_unknown'] = self.allow_unknown

            validator = self._get_child_validator(
                schema_crumb=(field, operator, i), schema=schema, allow_unknown=True
            )
            if validator(self.document, update=self.update, normalize=False):
                valid_counter += 1
            else:
                self._drop_nodes_from_errorpaths(validator._errors, [], [3])
                _errors.extend(validator._errors)

        return valid_counter, _errors

    def _validate_anyof(self, definitions, field, value):
        """ {'type': 'Sequence', 'logical': 'anyof'} """
        valids, _errors = self.__validate_logical('anyof', definitions, field, value)
        if valids < 1:
            self._error(field, errors.ANYOF, _errors, valids, len(definitions))

    def _validate_allof(self, definitions, field, value):
        """ {'type': 'Sequence', 'logical': 'allof'} """
        valids, _errors = self.__validate_logical('allof', definitions, field, value)
        if valids < len(definitions):
            self._error(field, errors.ALLOF, _errors, valids, len(definitions))

    def _validate_noneof(self, definitions, field, value):
        """ {'type': 'Sequence', 'logical': 'noneof'} """
        valids, _errors = self.__validate_logical('noneof', definitions, field, value)
        if valids > 0:
            self._error(field, errors.NONEOF, _errors, valids, len(definitions))

    def _validate_oneof(self, definitions, field, value):
        """ {'type': 'Sequence', 'logical': 'oneof'} """
        valids, _errors = self.__validate_logical('oneof', definitions, field, value)
        if valids != 1:
            self._error(field, errors.ONEOF, _errors, valids, len(definitions))

    def _validate_max(self, max_value, field, value):
        """ {'nullable': False } """
        try:
            if value > max_value:
                self._error(field, errors.MAX_VALUE)
        except TypeError:
            pass

    def _validate_min(self, min_value, field, value):
        """ {'nullable': False } """
        try:
            if value < min_value:
                self._error(field, errors.MIN_VALUE)
        except TypeError:
            pass

    def _validate_maxlength(self, max_length, field, value):
        """ {'type': 'integer'} """
        if isinstance(value, Iterable) and len(value) > max_length:
            self._error(field, errors.MAX_LENGTH, len(value))

    _validate_meta = dummy_for_rule_validation('')

    def _validate_minlength(self, min_length, field, value):
        """ {'type': 'integer'} """
        if isinstance(value, Iterable) and len(value) < min_length:
            self._error(field, errors.MIN_LENGTH, len(value))

    def _validate_nullable(self, nullable, field, value):
        """ {'type': 'boolean'} """
        if value is None:
            if not (nullable or self.ignore_none_values):
                self._error(field, errors.NULLABLE)
            self._drop_remaining_rules(
                'allowed',
                'empty',
                'forbidden',
                'items',
                'keysrules',
                'min',
                'max',
                'minlength',
                'maxlength',
                'regex',
                'schema',
                'type',
                'valuesrules',
            )

    def _validate_keysrules(self, schema, field, value):
        """ {'type': ('Mapping', 'string'), 'check_with': 'rulesset',
            'forbidden': ('rename', 'rename_handler')} """
        if isinstance(value, Mapping):
            validator = self._get_child_validator(
                document_crumb=field,
                schema_crumb=(field, 'keysrules'),
                schema={k: schema for k in value.keys()},
            )
            if not validator({k: k for k in value.keys()}, normalize=False):
                self._drop_nodes_from_errorpaths(validator._errors, [], [2, 4])
                self._error(field, errors.KEYSRULES, validator._errors)

    def _validate_readonly(self, readonly, field, value):
        """ {'type': 'boolean'} """
        if readonly:
            if not self._is_normalized:
                self._error(field, errors.READONLY_FIELD)
            # If the document was normalized (and therefore already been
            # checked for readonly fields), we still have to return True
            # if an error was filed.
            has_error = (
                errors.READONLY_FIELD
                in self.document_error_tree.fetch_errors_from(
                    self.document_path + (field,)
                )
            )
            if self._is_normalized and has_error:
                self._drop_remaining_rules()

    def _validate_regex(self, pattern, field, value):
        """ {'type': 'string'} """
        if not isinstance(value, str):
            return
        if not pattern.endswith('$'):
            pattern += '$'
        re_obj = re.compile(pattern)
        if not re_obj.match(value):
            self._error(field, errors.REGEX_MISMATCH)

    _validate_required = dummy_for_rule_validation(""" {'type': 'boolean'} """)

    _validate_require_all = dummy_for_rule_validation(""" {'type': 'boolean'} """)

    def __validate_required_fields(self, document):
        """ Validates that required fields are not missing.

        :param document: The document being validated.
        """
        required = set(
            field
            for field, definition in self.schema.items()
            if self._resolve_rules_set(definition).get('required', self.require_all)
        )
        required -= self._unrequired_by_excludes
        missing = required - set(
            field
            for field in document
            if document.get(field) is not None or not self.ignore_none_values
        )

        for field in missing:
            self._error(field, errors.REQUIRED_FIELD)

        # At least one field from self._unrequired_by_excludes should be present in
        # document.
        if self._unrequired_by_excludes:
            fields = set(field for field in document if document.get(field) is not None)
            if self._unrequired_by_excludes.isdisjoint(fields):
                for field in self._unrequired_by_excludes - fields:
                    self._error(field, errors.REQUIRED_FIELD)

    def _validate_schema(self, schema, field, value):
        """ {'type': ('Mapping', 'string'),
             'check_with': 'schema'} """

        if not isinstance(value, Mapping):
            return

        schema = self._resolve_schema(schema)
        allow_unknown = self.schema[field].get('allow_unknown', self.allow_unknown)
        require_all = self.schema[field].get('require_all', self.require_all)
        validator = self._get_child_validator(
            document_crumb=field,
            schema_crumb=(field, 'schema'),
            schema=schema,
            allow_unknown=allow_unknown,
            require_all=require_all,
        )
        if not validator(value, update=self.update, normalize=False):
            self._error(field, errors.SCHEMA, validator._errors)

    def _validate_type(self, data_type, field, value):
        """ {'type': 'tuple',
             'itemsrules': {
                 'oneof': (
                    {'type': 'string', 'check_with': 'type_names'},
                    {'type': ('type', 'generic_type_alias')}
                 )}} """
        if not data_type:
            return

        for _type in data_type:
            if isinstance(_type, str):
                type_definition = self.types_mapping[_type]
                if isinstance(value, type_definition.included_types) and not isinstance(
                    value, type_definition.excluded_types
                ):
                    return
            else:
                if isinstance(value, _type):
                    return

        self._error(field, errors.TYPE)
        self._drop_remaining_rules()

    def _validate_valuesrules(self, schema, field, value):
        """ {'type': ['dict', 'string'], 'check_with': 'rulesset',
            'forbidden': ['rename', 'rename_handler']} """
        if isinstance(value, Mapping):
            schema_crumb = (field, 'valuesrules')
            validator = self._get_child_validator(
                document_crumb=field,
                schema_crumb=schema_crumb,
                schema={k: schema for k in value},
            )
            validator(value, update=self.update, normalize=False)
            if validator._errors:
                self._drop_nodes_from_errorpaths(validator._errors, [], [2])
                self._error(field, errors.VALUESRULES, validator._errors)
