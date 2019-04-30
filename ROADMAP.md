# Cerberus development and support roadmap

This document lays out a roadmap for the further development of Cerberus in the
next few years, particularly in anticipation of the decay of Python 2.


## Assumptions

There are some assumptions that guide the following:

- The support of CPython 2.7 will end on January 1st, 2020.
  (See [Python Developer’s Guide](https://devguide.python.org/#status-of-python-branches))
- Supporting Python 2 and 3 comes with trade-offs.
- Everything is an object.


## Roadmap

### 1.3 release

The release is estimated to be ready in mid or late 2018.
The planned fixes and features are listed
[here](https://github.com/pyeve/cerberus/milestone/6).
It will contain a finalized version of this document.

### Branching off 1.3.x

After that release, a new branch `1.3.x` is created. This one will continue to
support Python 2 and receive bug fixes *at least* until December 31, 2019.
A *feature freeze* for functionality of the public API is declared.

#### Checklist

- [x] The `README.rst` and `CONTRIBUTING.rst` are updated accordingly.
- [ ] 1.3 is released.
- [ ] 1.3.x branch is created.

### Modernization and consolidation

This phase is designated to update the codebase with fundamental
implications.

#### Checklist

- [ ] All Python 2 related code is removed.
- [ ] Python 3 features that allow simpler code are applied where feasible.
  - [ ] A Python 3-style metaclass.
  - [ ] Using `super()` to call overridden methods.
  - [ ] Usage of dictionary comprehensions.
- [ ] All *public* functions and methods are type annotated. MyPy is added to 
      the test suite to validate these.
- [ ] A wider choice of type names that are closer oriented on the builtin
      names are available. (#374)
- [ ] Objects from the `typing` module can be used as constraints for the
      `type` rule. (#374)
- [ ] The `schema` rule only handles mappings, a new `itemrules` replaces the
      part where `schema` tested items in sequences so far. There will be no
      backward-compatibility for schemas. (#385)
- [ ] The rules `keyschema` and `valueschema` are renamed to `keyrules` and
      `valuerules`, backward-compatibility for schemas will be provided. (#385)
- [ ] Implementations of rules, coercers etc. can and the contributed should be
      qualified as such by metadata-annotating decorators. (With the intend to
      clean the code and make extensions simpler.) (#372)
- [ ] Dependency injection for all kind of handlers. (#279,#314)
- [ ] The feature freeze gets lifted and the `CONTRIBUTING.rst` is updated
      accordingly.
- [ ] The module `dataclasses` is implemented. This may get postponed 'til a
      following minor release. (#397)

#### Undecided issues

- Which Python version will be the minimum to support?
  - CPython 3.4 will be eol before 2.7 and 3.5 brings some extensions to the
    `inspect` module that would ease implementing a dependency injection.
- The name `itemrules`.
- Should the result be released as 2.0.a1?

### 2.0 release

After a series of release candidates, a final 2.0 with new features might be
available by the end of 2018.

#### Checklist

- [ ] The `DocumentError` exception is replaced with an error. (#141)
- [ ] Include a guide on upgrading from 1.x.
- [ ] Remove this document.
