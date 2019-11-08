# Cerberus development and support roadmap

This document lays out the roadmap towards the next major release, 2.0. It
will require at least Python 3.5 and break compatibility with previous
versions.

The 1.3 branch is and will be supported with bug fixes.

## 2.0-rc release

- [x] Deprecated features are removed.
- [x] The `schema` rule only handles mappings, a new `itemrules` replaces the
      part where `schema` tested items in sequences so far. There will be no
      backward-compatibility for schemas. (#385)
- [x] All Python 2 related code is removed.
- [x] Python 3 features that allow simpler code are applied where feasible.
  - [x] A Python 3-style metaclass.
  - [x] Using `super()` to call overridden methods.
  - [x] Usage of dictionary comprehensions.
- [x] All *public* functions and methods are type annotated. MyPy is added to
      the test suite to validate these.
- [x] A wider choice of type names that are closer oriented on the builtin
      names are available. (#374)
- [x] Objects from the `typing` module can be used as constraints for the
      `type` rule. (#374)
- [ ] Remove support for Python 3.4
- [ ] Implementations of rules, coercers etc. can and the contributed should be
      qualified as such by metadata-annotating decorators. (With the intend to
      clean the code and make extensions simpler.) (#372)
- [ ] Dependency injection for all kind of handlers. (#279,#314)
- [ ] The feature freeze gets lifted and the `CONTRIBUTING.rst` is updated
      accordingly.
- [ ] The module `dataclasses` is implemented. This may get postponed 'til a
      following minor release. (#397)
- [ ] The `DocumentError` exception is replaced with an error. (#141)
- [ ] Include a guide on upgrading from 1.x.
- [ ] Update `docs/index.rst` regarding the supported branches 

## 2.0 release

- [ ] Remove this document.
