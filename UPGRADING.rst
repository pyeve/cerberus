Upgrading to Cerberus 1.0
=========================

Major Additions
---------------

Error Handling
..............

The inspection on and representation of errors is thoroughly overhauled and
allows a more detailed and flexible handling. Make sure you have look on
:doc:`errors`.

Also, :attr:`~cerberus.Validator.errors` (as provided by the default
:class:`~cerberus.errors.BasicErrorHandler`) values are lists containing
error messages, and possibly a ``dict`` as last item containing nested errors.
Previously, they were strings if single errors per field occurred; lists
otherwise.


Deprecations
------------

``Validator`` class
...................

transparent_schema_rules
~~~~~~~~~~~~~~~~~~~~~~~~

In the past you could override the schema validation by setting
``transparent_schema_rules`` to ``True``. Now all rules whose implementing
method's docstring contain a schema to validate the arguments for that rule in the
validation schema, are validated.
To omit the schema validation for a particular rule, just omit that definition,
but consider it a bad practice.
The :class:`~cerberus.Validator`-attribute and -initialization-argument
``transparent_schema_rules`` are removed without replacement.

validate_update
~~~~~~~~~~~~~~~

The method ``validate_update`` has been removed from
:class:`~cerberus.Validator`. Instead use :meth:`~cerberus.Validator.validate`
with the keyword-argument ``update`` set to ``True``.


Rules
.....

items (for mappings)
~~~~~~~~~~~~~~~~~~~~

The usage of the ``items``-rule is restricted to sequences.
If you still had schemas that used that rule to validate
:term:`mappings <mapping>`, just rename these instances to ``schema``
(:ref:`docs <schema_dict-rule>`).

keyschema & valueschema
~~~~~~~~~~~~~~~~~~~~~~~

To reflect the common terms in the Pythoniverse [#]_, the rule for validating
all *values* of a :term:`mapping` was renamed from ``keyschema`` to
``valueschema``. Furthermore a rule was implemented to validate all *keys*,
introduced as ``propertyschema``, now renamed to ``keyschema``. This means code
using prior versions of cerberus would not break, but bring up wrong results!

To update your code you may adapt cerberus' iteration:

  1. Rename ``keyschema`` to ``valueschema`` in your schemas. (``0.9``)
  2. Rename ``propertyschema`` to ``keyschema`` in your schemas. (``1.0``)

Note that ``propertyschema`` will *not* be handled as an alias like
 ``keyschema`` was in the ``0.9``-branch.


Custom validators
.................

Data types
~~~~~~~~~~

Since the ``type``-rule allowed multiple arguments cerberus' type validation
code was somewhat cumbersome as it had to deal with the circumstance that each
type checking method would file an error though another one may not - and thus
positively validate the constraint as a whole.
The refactoring of the error handling allows cerberus' type validation to be
much more lightweight and to formulate the corresponding methods in a simpler
way.

Previously such a method would test what a value *is not* and submit an error.
Now a method tests what a value *is* to be expected and returns ``True`` in
that case.

This is the most critical part of updating your code, but still easy when your
head is clear. Of course your code is well tested. It's essentially these
three steps. Search, Replace and Regex may come at your service.

  1. Remove the second method's argument (probably named ``field``).
  2. Invert the logic of the conditional clauses where is tested what a value
     is not / has not.
  3. Replace calls to ``self._error`` below such clauses with
     ``return True``.

A method doesn't need to return ``False`` or any value when expected criteria
are not met.

Here's the change from the :ref:`documentation <new-types>` example.

pre-1.0:

.. code-block:: python

     def _validate_type_objectid(self, field, value):
         if not re.match('[a-f0-9]{24}', value):
             self._error(field, errors.BAD_TYPE)

1.0:

.. code-block:: python

     def _validate_type_objectid(self, value):
         if re.match('[a-f0-9]{24}', value):
             return True



.. [#] compare :term:`dictionary`
