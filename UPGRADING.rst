Upgrading to cerberus 1.0
=========================


Document status
---------------

This is a draft and will be finalised with the 1.0(-RC?) release of cerberus.

TODO:

  - link appropriate sections in the docs


Deprecations
------------

keyschema & valueschema
~~~~~~~~~~~~~~~~~~~~~~~

To reflect the common terms in the Pythoniverse [#]_, the rule for validating
all *values* of a :term:`mapping` was renamed from ``keyschema`` to
``valueschema``. Furthermore a rule was implemented to validate all *keys*,
introduced as ``propertyschema``, now renamed to ``keyschema``. This means code
using prior versions of cerberus would not break, but result in wrong results!

To update your code you may adapt cerberus' iteration:

  1. Rename ``keyschema`` to ``valueschema`` in your schemas. (``0.9``)
  2. Rename ``propertyschema`` to ``keyschema`` in your schemas. (``1.0``)

Note that ``propertyschema`` will *not* be handled as an alias like
 ``keyschema`` was in the ``0.9``-branch.


.. [#] compare :term:`dictionary`
