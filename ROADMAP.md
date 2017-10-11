# Cerberus development and support roadmap

This document lays out a roadmap for the further development of Cerberus in the
next few years, particularly in anticipation of the decay of Python 2.
The current status is a **draft**, pull requests for changes are welcome.


## Assumptions

There are some assumptions that guide the following:

- The support of CPython 2.7 will end on April 12, 2020.
- Supporting Python 2 and 3 comes with trade-offs.
- Everything is an object.


## Roadmap

### 1.2 release

The release is estimated to be ready at the end of 2017.
The planned fixes and features are listed 
[here](https://github.com/pyeve/cerberus/milestone/5).
It will contain a finalized version of this document.

### Branching off 1.x

After that release, a new branch `1.x` is created. It will continue to support
Python 2 and receive bug fixes *at least* until December 31, 2019.
A *feature freeze* for functionality of the public API is declared.

#### Checklist

- [ ] The `README.rst` and `CONTRIBUTING.rst` are updated accordingly.
- [ ] 1.2 is released.
- [ ] 1.x branch is created.

#### Undecided issues

- Shall we start releasing micro / patch releases from here on?

### Modernization and consolidation

This phase is designated to update the codebase with fundamental
implications.

#### Checklist

- [ ] All Python 2 related code is removed.
- [ ] Python 3 features that allow simpler code are applied where feasible are
      used.
  - [ ] A Python 3-style metaclass.
- [ ] All functions and methods are type annotated. MyPy is added to the test
      suite.
- [ ] A wider choice of type names that are closer oriented on the builtin
      names are available. (#tba)
- [ ] Objects from the `typing` module can be used as constraints for the 
      `type` rule.
- [ ] The `schema` rule only handles mappings, a new `itemrules` replaces the
      part where `schema` tested items in sequences so far.
- [ ] Handlers for rules, coercers etc. can and the contributed should be
      qualified as such by metadata-annotating decorators. (With the intend to
      clean the code and make extensions simpler.)
- [ ] The feature freeze gets lifted and the `CONTRIBUTING.rst` is updated
      accordingly.

#### Undecided issues

- Which Python version will be the minimum to support?
- The name `itemrules`.
- Should the result be released as 2.0.a1?

### 2.0 release

After a series of release candidates, a final 2.0 with new features might be
available in the middle of 2018.

#### Checklist

- [ ] The `DocumentError` exception is replaced with an error. (#141)
- [ ] Dependency injection for all kind of handlers. (#279,#314)
- [ ] A convenient way for document processing chains and branches. (#tba)
- [ ] Include a guide on upgrading from 1.x.
- [ ] Remove this document.
