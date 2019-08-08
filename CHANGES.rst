Cerberus Changelog
==================

Cerberus is a collaboratively funded project, see the `funding page`_.

Version 1.3.2
-------------

Unreleased.

New
~~~

- Support for Python 3.8

Fixed
~~~~~

- Fixed the message of the ``BasicErrorHandler`` for an invalid amount of items
  (`#505`_)

.. _`#505`: https://github.com/pyeve/cerberus/issues/505

Version 1.3.1
-------------

Releases on May 10, 2019.

Fixed
~~~~~

- Fixed the expansion of the deprecated rule names ``keyschema`` and
  ``valueschema`` (`#482`_)
- ``*of_``-typesavers properly expand rule names containing ``_`` (`#484`_)

Improved
~~~~~~~~
- Add ``maintainer`` and ``maintainer_email`` to setup.py (`#481`_)
- Add ``project_urls`` to setup.py (`#480`_)
- Don't ignore all exceptions during coercions for nullable fields. If a
- Coercion raises an exception for a nullable field where the field is not
  ``None`` the validation now fails. (`#490`_)

.. _`#490`: https://github.com/pyeve/cerberus/issues/490
.. _`#484`: https://github.com/pyeve/cerberus/issues/484
.. _`#482`: https://github.com/pyeve/cerberus/issues/482
.. _`#481`: https://github.com/pyeve/cerberus/issues/481
.. _`#480`: https://github.com/pyeve/cerberus/issues/480

Version 1.3
-----------

Releases on April 30, 2019.

New
~~~
- Add ``require_all`` rule and validator argument (`#417`_)
- The ``contains`` rule (`#358`_)
- All fields that are defined as ``readonly`` are removed from a document
  when a validator has the ``purge_readonly`` flag set to ``True`` (`#240`_)
- The ``validator`` rule is renamed to ``check_with``. The old name is
  deprecated and will not be available in the next major release of Cerberus
  (`#405`_)
- The rules ``keyschema`` and ``valueschema`` are renamed to ``keysrules`` and
  ``valuesrules``; the old names are deprecated and will not be available in
  the next major release of Cerbers (`#385`_)
- The ``meta`` pseudo-rule can be used to store arbitrary application data
  related to a field in a schema
- Python 3.7 officially supported (`#451`_)
- **Python 2.6 and 3.3 are no longer supported**

Fixed
~~~~~
- Fix test test_{default,default_setter}_none_nonnullable (`#435`_)
- Normalization rules defined within the ``items`` rule are applied (`#361`_)
- Defaults are applied to undefined fields from an ``allow_unknown``
  definition (`#310`_)
- The ``forbidden`` value now handles any input type (`#449`_)
- The `allowed` rule will not be evaluated on fields that have a legit ``None``
  value (`#454`_)
- If the cerberus distribution cannot not be found, the version is set to the
  value ``unknown`` (`#472`_)

Improved
~~~~~~~~
- Suppress DeprecationWarning about collections.abc (`#451`_)
- Omit warning when no schema for ``meta`` rule constraint is available
  (`#425`_)
- Add ``.eggs`` to .gitignore file (`#420`_)
- Reformat code to match Black code-style (`#402`_)
- Perform lint checks and fixes on staged files, as a pre-commit hook (`#402`_)
- Change ``allowed`` rule to use containers instead of lists (`#384`_)
- Remove ``Registry`` from top level namespace (`#354`_)
- Remove ``utils.is_class``
- Check the ``empty`` rule against values of type ``Sized``
- Various micro optimizations and 'safety belts' that were inspired by adding
  type annotations to a branch of the code base

Docs
~~~~
- Fix semantical versioning naming. There are only two hard things in Computer
  Science: cache invalidation and naming things -- *Phil Karlton* (`#429`_)
- Improve documentation of the regex rule (`#389`_)
- Expand upon `validator` rules (`#320`_)
- Include all errors definitions in API docs (`#404`_)
- Improve changelog format (`#406`_)
- Update homepage URL in package metadata (`#382`_)
- Add feature freeze note to CONTRIBUTING and note on Python support in
  README
- Add the intent of a ``dataclasses`` module to ROADMAP.md
- Update README link; make it point to the new PyPI website
- Update README with elaborations on versioning and testing
- Fix misspellings and missing pronouns
- Remove redundant hint from ``*of-rules``.
- Add usage recommendation regarding the ``*of-rules``
- Add a few clarifications to the GitHub issue template
- Update README link; make it point to the new PyPI website

.. _`#472`: https://github.com/pyeve/cerberus/pull/472
.. _`#454`: https://github.com/pyeve/cerberus/pull/454
.. _`#451`: https://github.com/pyeve/cerberus/pull/451
.. _`#449`: https://github.com/pyeve/cerberus/pull/449
.. _`#435`: https://github.com/pyeve/cerberus/pull/435
.. _`#429`: https://github.com/pyeve/cerberus/pull/429
.. _`#425`: https://github.com/pyeve/cerberus/pull/425
.. _`#420`: https://github.com/pyeve/cerberus/issues/420
.. _`#417`: https://github.com/pyeve/cerberus/issues/417
.. _`#406`: https://github.com/pyeve/cerberus/issues/406
.. _`#405`: https://github.com/pyeve/cerberus/issues/405
.. _`#404`: https://github.com/pyeve/cerberus/issues/404
.. _`#402`: https://github.com/pyeve/cerberus/issues/402
.. _`#389`: https://github.com/pyeve/cerberus/issues/389
.. _`#385`: https://github.com/pyeve/cerberus/issues/385
.. _`#384`: https://github.com/pyeve/cerberus/issues/384
.. _`#382`: https://github.com/pyeve/cerberus/issues/382
.. _`#361`: https://github.com/pyeve/cerberus/pull/361
.. _`#358`: https://github.com/pyeve/cerberus/issues/358
.. _`#354`: https://github.com/pyeve/cerberus/issues/354
.. _`#320`: https://github.com/pyeve/cerberus/issues/320
.. _`#310`: https://github.com/pyeve/cerberus/issues/310
.. _`#240`: https://github.com/pyeve/cerberus/issues/240

Version 1.2
-----------

Released on April 12, 2018.

- New: docs: Add note that normalization cannot be applied within an ``*of-rule``.
  (Frank Sachsenheim)
- New: Add the ability to query for a type of error in an error tree.
  (Frank Sachsenheim)
- New: Add errors.MAPPING_SCHEMA on errors within subdocuments.
  (Frank Sachsenheim)
- New: Support for Types Definitions, which allow quick types check on the fly.
  (Frank Sachsenheim)

- Fix: Simplify the tests with Docker by using a volume for tox environments.
  (Frank Sachsenheim)
- Fix: Schema registries do not work on dict fields.
  Closes :issue:`318`. (Frank Sachsenheim)
- Fix: Need to drop some rules when ``empty`` is allowed.
  Closes :issue:`326`. (Frank Sachsenheim)
- Fix: typo in README (Christian Hogan)
- Fix: Make ``purge_unknown`` and ``allow_unknown`` play nice together.
  Closes :issue:`324`. (Audric Schiltknecht)
- Fix: API reference lacks generated content.
  Closes :issue:`281`. (Frank Sachsenheim)
- Fix: ``readonly`` works properly just in the first validation.
  Closes :issue:`311`. (Frank Sachsenheim)
- Fix: ``coerce`` ignores ``nullable: True``.
  Closes :issue:`269`. (Frank Sachsenheim)
- Fix: A dependency is not considered satisfied if it has a null value.
  Closes :issue:`305`. (Frank Sachsenheim)
- Override ``UnvalidatedSchema.copy``. (Peter Demin)
- Fix: README link. (Gabriel Wainer)
- Fix: Regression: allow_unknown causes dictionary validation to fail with
  a KeyError. Closes :issue:`302`. (Frank Sachsenheim)
- Fix: Error when setting fields as tuples instead of lists.
  Closes :issue:`271`. (Sebastian Rajo)
- Fix: Correctly handle nested logic and group errors.
  Closes :issue:`278` and :issue:`299`. (Kornelijus Survila)
- CI: Reactivate testing on PyPy3. (Frank Sachsenheim)

Version 1.1
-----------

Released on January 25, 2017.

- New: Python 3.6 support. (Frank Sachsenheim)
- New: Users can implement their own semantics in Validator._lookup_field.
  (Frank Sachsenheim)
- New: Allow applying of ``empty`` rule to sequences and mappings.
  Closes :issue:`270`. (Frank Sachsenheim)

- Fix: Better handling of unicode in ``allowed`` rule.
  Closes :issue:`280`. (Michael Klich).
- Fix: Rules sets with normalization rules fail.
  Closes :issue:`283`. (Frank Sachsenheim)
- Fix: Spelling error in RULE_SCHEMA_SEPARATOR constant (Antoine Lubineau)
- Fix: Expand schemas and rules sets when added to a registry. Closes :issue:`284`
  (Frank Sachsenheim)
- Fix: ``readonly`` conflicts with ``default`` rule. Closes :issue:`268` (Dominik
  Kellner).
- Fix: Creating custom Validator instance with ``_validator_*`` method raises
  ``SchemaError``. Closes :issue:`265` (Frank Sachsenheim).
- Fix: Consistently use new style classes (Dominik Kellner).
- Fix: ``NotImplemented`` does not derive from ``BaseException``. (Bryan W.
  Weber).

- Completely switch to py.test. Closes :issue:`213` (Frank Sachsenheim).
- Convert ``self.assert`` method calls to plain ``assert`` calls supported by
  pytest. Addresses :issue:`213` (Bruno Oliveira).

- Docs: Clarifications concerning dependencies and unique rules. (Frank
  Sachsenheim)
- Docs: Fix custom coerces documentation. Closes :issue:`285`. (gilbsgilbs)
- Docs: Add note concerning regex flags. Closes :issue:`173`. (Frank Sachsenheim)
- Docs: Explain that normalization and coercion are performed on a copy of the
  original document (Sergey Leshchenko)

Version 1.0.1
-------------

Released on September 1, 2016.

- Fix: bump trove classifier to Production/Stable (5).

Version 1.0
-----------

Released on September 1, 2016.

.. warning::

    This is a major release which breaks backward compatibility in several
    ways. Don't worry, these changes are for the better. However, if you are
    upgrading, then you should really take the time to read the list of
    `Breaking Changes`_ and consider their impact on your codebase. For your
    convenience, some :doc:`upgrade notes <upgrading>` have been included.

- New: Add capability to use references in schemas. (Frank Sachsenheim)
- New: Support for binary type. (Matthew Ellison)
- New: Allow callables for 'default' schema rule. (Dominik Kellner)
- New: Support arbitrary types with 'max' and 'min' (Frank Sachsenheim).
- New: Support any iterable with 'minlength' and 'maxlength'.
  Closes :issue:`158`. (Frank Sachsenheim)
- New: 'default' normalization rule. Closes :issue:`131`. (Damián Nohales)
- New: 'excludes' rule (calve). Addresses :issue:`132`.
- New: 'forbidden' rule. (Frank Sachsenheim)
- New: 'rename'-rule renames a field to a given value during normalization
  (Frank Sachsenheim).
- New: 'rename_handler'-rule that takes an callable that renames unknown
  fields. (Frank Sachsenheim)
- New: 'Validator.purge_unknown'-property and conditional purging of unknown
  fields. (Frank Sachsenheim)
- New: 'coerce', 'rename_handler' and 'validator' can use class-methods (Frank
  Sachsenheim).
- New: '*of'-rules can be extended by concatenating another rule. (Frank
  Sachsenheim)
- New: Allows various error output with error handlers (Frank Sachsenheim).
- New: Available rules etc. of a Validator-instance are accessible as
  'validation_rules', 'normalization_rules', 'types', 'validators' and
  'coercer' -property. (Frank Sachsenheim)
- New: Custom rule's method docstrings can contain an expression to validate
  constraints for that rule when a schema is validated. (Frank Sachsenheim).
- New: 'Validator.root_schema' complements 'Validator.root_document'. (Frank
  Sachsenheim)
- New: 'Validator.document_path' and 'Validator.schema_path' properties can
  be used to determine the relation of the currently validating document to the
  'root_document' / 'root_schema'. (Frank Sachsenheim)
- New: Known, validated definition schemas are cached, thus validation run-time
  of schemas is reduced. (Frank Sachsenheim)
- New: Add testing with Docker. (Frank Sachsenheim)
- New: Support CPython 3.5. (Frank Sachsenheim)

- Fix: 'allow_unknown' inside *of rule is ignored. Closes #251. (Davis
  Kirkendall)
- Fix: unexpected TypeError when using allow_unknown in a schema defining
  a list of dicts. Closes :issue:`250`. (Davis Kirkendall)
- Fix: validate with 'update=True' does not work when required fields are in
  a list of subdicts. (Jonathan Huot)
- Fix: 'number' type fails if value is boolean.
  Closes :issue:`144`. (Frank Sachsenheim)
- Fix: allow None in 'default' normalization rule. (Damián Nohales)
- Fix: in 0.9.2, coerce does not maintain proper nesting on dict fields. Closes
  :issue:`185`.
- Fix: normalization not working for valueschema and propertyschema. Closes
  :issue:`155`. (Frank Sachsenheim)
- Fix: 'coerce' on List elements produces unexpected results.
  Closes :issue:`161`. (Frank Sachsenheim)
- Fix: 'coerce'-constraints are validated. (Frank Sachsenheim)
- Fix: Unknown fields are normalized. (Frank Sachsenheim)
- Fix: Dependency on boolean field now works as expected.
  Addresses :issue:`138`. (Roman Redkovich)
- Fix: Add missing deprecation-warnings. (Frank Sachsenheim)

- Docs: clarify read-only rule. Closes :issue:`127`.
- Docs: split Usage page into Usage; Validation Rules: Normalization Rules.
  (Frank Sachsenheim)

Breaking Changes
~~~~~~~~~~~~~~~~
Several relevant breaking changes have been introduced with this release. For
the inside scoop, please see the :doc:`upgrade notes <upgrading>`.

- Change: 'errors' values are lists containing error messages. Previously, they
  were simple strings if single errors, lists otherwise.
  Closes :issue:`210`. (Frank Sachsenheim)
- Change: Custom validator methods: remove the second argument.
  (Frank Sachsenheim)
- Change: Custom validator methods: invert the logic of the conditional clauses
  where is tested what a value is not / has not. (Frank Sachsenheim)
- Change: Custom validator methods: replace calls to 'self._error' with
  'return True', or False, or None. (Frank Sachsenheim)
- Change: Remove 'transparent_schema_rule' in favor of docstring schema
  validation. (Frank Sachsenheim)
- Change: Rename 'property_schema' rule to 'keyschema'. (Frank Sachsenheim)
- Change: Replace 'validate_update' method with 'update' keywork argument.
  (Frank Sachsenheim)
- Change: The processed root-document of is now available as 'root_document'-
  property of the (child-)Validator. (Frank Sachsenheim)
- Change: Removed 'context'-argument from 'validate'-method as this is set
  upon the creation of a child-validator. (Frank Sachsenheim)
- Change: 'ValidationError'-exception renamed to 'DocumentError'.
  (Frank Sachsenheim)
- Change: Consolidated all schema-related error-messages' names.
  (Frank Sachsenheim)
- Change: Use warnings.warn for deprecation-warnings if available.
  (Frank Sachsenheim)

Version 0.9.2
-------------

Released on September 23, 2015

- Fix: don't rely on deepcopy since it can't properly handle complex objects in
  Python 2.6.

Version 0.9.1
-------------

Released on July 7 2015

- Fix: 'required' is always evaluated, independent of eventual missing
  dependencies. This changes the previous behaviour whereas a required field
  with dependencies would only be reported as missing if all dependencies were
  met. A missing required field will always be reported. Also see the
  discussion in https://github.com/pyeve/eve/pull/665.

Version 0.9
-----------

Released on June 24 2015.
Codename: 'Mastrolindo'.

- New: 'oneof' rule which provides a list of definitions in which only one
  should validate (C.D. Clark III).
- New: 'noneof' rule which provides a list of definitions that should all not
  validate (C.D. Clark III).
- New: 'anyof' rule accepts a list of definitions and checks that one
  definition validates (C.D. Clark III).
- New: 'allof' rule validates if if all definitions validate (C.D. Clark III).
- New: 'validator.validated' takes a document as argument and returns
  a validated document or 'None' if validation failed (Frank Sachsenheim).
- New: PyPy support (Frank Sachsenheim).
- New: Type coercion (Brett).
- New: Added 'propertyschema' validation rule (Frank Sachsenheim).

- Change: Use 'str.format' in error messages so if someone wants to override
  them does not get an exception if arguments are not passed.
  Closes :issue:`105`. (Brett)
- Change: 'keyschema' renamed to 'valueschema', print a deprecation warning
  (Frank Sachsenheim).
- Change: 'type' can also be a list of types (Frank Sachsenheim).

- Fix: useages of 'document' to 'self.document' in '_validate' (Frank
  Sachsenheim).
- Fix: when 'items' is applied to a list, field name is used as key for
  'validator.errors', and offending field indexes are used as keys for field
  errors ({'a_list_of_strings': {1: 'not a string'}}) 'type' can be a list of
  valid types.
- Fix: Ensure that additional `**kwargs` of a subclass persist through
  validation (Frank Sachsenheim).
- Fix: improve failure message when testing against multiple types (Frank
  Sachsenheim).
- Fix: ignore 'keyschema' when not a mapping (Frank Sachsenheim).
- Fix: ignore 'schema' when not a sequence (Frank Sachsenheim).
- Fix: allow_unknown can also be set for nested dicts.
  Closes :issue:`75`. (Tobias Betz)
- Fix: raise SchemaError when an unallowed 'type' is used in conjunction with
  'schema' rule (Tobias Betz).

- Docs: added section that points out that YAML, JSON, etc. can be used to
  define schemas (C.D. Clark III).
- Docs: Improve 'allow_unknown' documentation (Frank Sachsenheim).

Version 0.8.1
-------------

Released on Mar 16 2015.

- Fix: dependency on a sub-document field does not work. Closes :issue:`64`.
- Fix: readonly validation should happen before any other validation.
  Closes :issue:`63`.
- Fix: allow_unknown does not apply to sub-dictionaries in a list.
  Closes :issue:`67`.
- Fix: two tests being ignored because of name typo.
- Fix: update mode does not ignore required fields in subdocuments.
  Closes :issue:`72`.
- Fix: allow_unknown does not respect custom rules. Closes :issue:`66`.
- Fix: typo in docstrings (Riccardo).

Version 0.8
-----------

Released on Jan 7 2015.

- 'dependencies' also supports dependency values.
- 'allow_unknown' can also be set to a validation schema, in which case unknown
  fields will be validated against it. Closes pyeve/eve:issue:`405`.
- New function-based custom validation mode (Luo Peng).
- Fields with empty definitions in schema were reported as non-existent. Now
  they are considered as valid, whatever their value is (Jaroslav Semančík).
- If dependencies are precised for a 'required' field, then the presence of the
  field is only validated if all dependencies are present (Trong Hieu HA).
- Documentation typo (Nikita Vlaznev :issue:`55`).
- [CI] Add travis_retry to pip install in case of network issues (Helgi Þormar
  Þorbjörnsson :issue:`49`)

Version 0.7.2
-------------

Released on Jun 19 2014.

- Successfully validate int as float type (Florian Rathgeber).

Version 0.7.1
-------------

Released on Jun 17 2014.

- Validation schemas are now validated up-front. When you pass a Schema to the
  Validator it will be validated against the supported ruleset (Paul Weaver).
  Closes :issue:`39`.
- Custom validators also have access to a special 'self.document' variable that
  allows validation of a field to happen in context of the rest of the document
  (Josh Villbrandt).
- Validator options like 'allow_unknown' and 'ignore_none_values' are now taken
  into consideration when validating sub-dictionaries. Closes :issue:`40`.

Version 0.7
-----------

Released on May 16 2014.

- Python 3.4 is now supported.
- tox support.
- Added 'dependencies' validation rule (Lujeni).
- Added 'keyschema' validation rule (Florian Rathgeber).
- Added 'regex' validation rule. Closes :issue:`29`.
- Added 'set' as a core data type. Closes :issue:`31`.
- Not-nullable fields are validated independetly of their type definition
  (Jaroslav Semančík).
- Python trove classifiers added to setup.py. Closes :issue:`32`.
- 'min' and 'max' now apply to floats and numbers too. Closes :issue:`30`.

Version 0.6
-----------

Released on February 10 2014

- Added 'number' data type, which validates against both float and integer
  values (Brandon Aubie).
- Added support for running tests with py.test
- Fix non-blocking problem introduced with 0.5 (Martin Ortbauer).
- Fix bug when _error() is calld twice for a field (Jaroslav Semančík).
- More precise error message in rule 'schema' validation (Jaroslav Semančík).
- Use 'allowed' field for integer just like for string (Peter Demin).

Version 0.5
-----------

Released on December 4 2013

- 'validator.errors' now returns a dictionary where keys are document fields
  and values are lists of validation errors for the field.
- Validator instances are now callable. Instead of `validated
  = validator.validate(document)` you can now choose to do 'validated
  = validator(document)' (Eelke Hermens).

Version 0.4.0
-------------

Released on September 24 2013.

- 'validate_update' is deprecated and will be removed with next release. Use
  'validate' with 'update=True' instead. Closes :issue:`21`.
- Fixed a minor encoding issue which made installing on Windows/Python3
  impossible. Closes :issue:`19` (Arsh Singh).
- Fix documentation typo (Daniele Pizzolli).
- 'type' validation is always performed first (only exception being
  'nullable'). On failure, subsequent rules on the same field are skipped.
  Closes :issue:`18`.

Version 0.3.0
-------------

Released on July 9 2013.

- docstrings now conform to PEP8.
- `self.errors` returns an empty list if validate() has not been called.
- added validation for the 'float' data type.
- 'nullable' rule added to allow for null field values to be accepted in
  validations. This is different than required in that you can actively change
  a value to None instead of omitting or ignoring it. It is essentially the
  ignore_none_values, allowing for more fine grained control down to the field
  level (Kaleb Pomeroy).

Version 0.2.0
-------------

Released on April 18 2013.

- 'allow_unknown' option added.

Version 0.1.0
-------------

Released on March 15 2013.
Codename: 'Claw'.

- entering beta phase.
- support for Python 3.
- pep8 and pyflakes fixes (Harro van der Klauw).
- removed superflous typecheck for empty validator (Harro van der Klauw).
- 'ignore_none_values' option to ignore None values when type checking (Harro
  van der Klauw).
- 'minlenght' and 'maxlength' now apply to lists as well (Harro van der Klauw).


Version 0.0.3
-------------

Released on January 29 2013

- when a list item fails, its offset is now returned along with the list name.
- 'transparent_schema_rules' option added.
- 'empty' rule for string fields.
- 'schema' rule on lists of arbitrary lenght (Martjin Vermaat).
- 'allowed' rule on strings (Martjin Vermaat).
- 'items' (dict) is now deprecated. Use the upgraded 'schema' rule instead.
- AUTHORS file added to sources.
- CHANGES file added to sources.


Version 0.0.2
-------------

Released on November 22 2012.

- Added support for addition and validation of custom data types.
- Several documentation improvements.

Version 0.0.1
-------------

Released on October 16 2012.

First public preview release.

.. _`upgrade notes`: upgrading
.. _`funding page`: http://docs.python-cerberus.org/en/stable/funding.html
