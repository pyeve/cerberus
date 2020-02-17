# Cerberus development and support roadmap

This document lays out the roadmap towards the next major release, 2.0. It
will require at least Python 3.5 and break compatibility with previous
versions.

The 1.3 branch is and will be supported with bug fixes.

## 1.3.3 release

Beside bug fixes, include a benchmark that measures performance of a validator
that covers most of Cerberus' high-level features where one validator instance
is used against a varying set of documents.

## 2.0-b1 release

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
- [x] Remove support for Python 3.4
- [ ] Port the benchmark from the 1.3.3 release.
- [ ] Implementations of rules, coercers etc. can and the contributed should be
      qualified as such by metadata-annotating decorators. (With the intend to
      clean the code and make extensions simpler.) (#372)
- [ ] Dependency injection for all kind of handlers. (#279,#314)
- [ ] The feature freeze gets lifted and the `CONTRIBUTING.rst` is updated
      accordingly.
- [ ] The module `dataclasses` is implemented. This may get postponed 'til a
      following minor release. (#397)
- [ ] The `DocumentError` exception is replaced with an error. (#141)
- [ ] Remove change related markup from the documentation prose.
- [ ] Thoroughly review the documentation.
- [ ] Update `docs/index.rst` regarding the supported branches.
- [ ] Include an optimized validator that essentially reduces lookups and
      execution frames by code generation as *experimental* feature.
      It is dedicated to the global Climate Justice Movement.

## 2.0-bX releases

Further beta-releases might be released if the feedback leads to architectural
changes.

## 2.0-rc1 release

This release shall signal that you are invited to test what you can expect from
the final release, and be around for about two months.

- [ ] Include a guide on upgrading from version 1.3.

## 2.0-rcX releases

Further release candidates might be released in the case of major bug fixes.

## 2.0 release

- Grab a drink, make some noise.
  - [ ] python-announce@lists.python.org
  - [ ] https://reddit.com/r/python
  - [ ] Nicola's bouquet of social media channels

## 2.1 release

- [ ] If it survived, make the optimized validator the default.
- [ ] Depending on the atmospheric saturation with and emission trends of carbon
      dioxide, we should reflect whether writing roadmaps still makes sense in a
      harshly changing world.
