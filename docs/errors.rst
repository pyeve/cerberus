Errors & Error Handling
=======================

Errors can be evaluated via Python interfaces or be processed to different
output formats with error handlers.


Error Handlers
--------------

Error handlers will return different output via the
:attr:`~cerberus.Validator.errors` property of a validator after the processing
of a document. The error handler to be used can be passed as keyword-argument
``error_handler`` to the initialization of a validator or by setting it's
property with the same name at any time. On initialization either an instance
or a class can be provided. If a class is provided, a dictionary with keyword-
arguments for initialization can be passed as ``error_handler_config``.

The following handlers are available:

  - :class:`~cerberus.errors.BasicErrorHandler`: This is the **default** that
    returns a (possibly nested) dictionary. The keys refer to the document's
    ones and the values contain an error message or a list of them.


Python interfaces
-----------------

An error is represented as :class:`~cerberus.errors.ValidationError` that has
the following properties:

  - ``document_path``: The path within the document. For flat dictionaries
    this simply be a key's name in a tuple, for nested ones it's all traversed
    key names. Items in sequences are represented by their index.
  - ``schema_path``: The path within the schema.
  - ``code``: The unique identifier for an error. See :mod:`~cerberus.errors`
    for a list.
  - ``rule``: The rule that was evaluated when the error occurred.
  - ``constraint``: That rule's constraint.
  - ``value``: The value being validated.
  - ``info``: This tuple contains additional informations that were submitted
    with the error. For most errors this is actually nothing. For bulk
    validations (e.g. with ``items`` or ``propertyschema``) this property keeps
    all individual errors.
    See the implementation of a rule in the source code to figure out its
    additional logging.

.. warning::

    As this is a fresh addition, the additional ``info`` that is logged *may*
    change during beta. If you have an urge for sustainability, please
    :doc:`open an issue <contact>`.

You can access the errors per these properties of a :class:`~cerberus.Validator`
instance after a processing of a document:

  - ``_errors``: This list holds all submitted errors. It is not intended to
    manipulate errors directly via this attribute.

  - ``document_error_tree``: A ``dict``-like object that allows you to query
    nodes corresponding to your document. That node's errors are contained in
    its :attr:`errors` property and are yielded when iterating over a node.
    If no errors occurred in a node or below, ``None`` will be returned
    instead.

  - ``schema_error_tree``: Similarly for the used schema.

.. versionchanged:: 0.10
    Errors are stored as :class:`~cerberus.errors.ValidationError` in a list.

Examples
~~~~~~~~

.. doctest::

    >>> schema = {'cats': {'type': 'integer'}}
    >>> document = {'cats': 'two'}
    >>> v.validate(document, schema)
    False
    >>> v.document_error_tree['cats'].errors == v.schema_error_tree['cats']['type'].errors
    True
    >>> error = v.document_error_tree['cats'].errors[0]
    >>> error.document_path
    ('cats',)
    >>> error.schema_path
    ('cats', 'type')
    >>> error.rule
    'type'
    >>> error.constraint
    'integer'
    >>> error.value
    'two'
