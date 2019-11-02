How to Contribute
=================

Contributions are welcome! Not familiar with the codebase yet? No problem!
There are many ways to contribute to open source projects: reporting bugs,
helping with the documentation, spreading the word and of course, adding
new features and patches.

.. note::

    There's currently a feature freeze until the basic code modernization for
    the 2.0 release is finished. Have a look at the ``ROADMAP.md`` for a status
    on its progress.

Getting Started
---------------
#. Make sure you have a GitHub account.
#. Open a `new issue`_, assuming one does not already exist.
#. Clearly describe the issue including steps to reproduce when it is a bug.

Making Changes
--------------
* Fork_ the repository on GitHub.
* Create a topic branch from where you want to base your work.
* This is usually the ``master`` branch.
* Please avoid working directly on ``master`` branch.
* Make commits of logical units (if needed rebase your feature branch before
  submitting it).
* Make sure your commit messages are in the `proper format`_.
* If your commit fixes an open issue, reference it in the commit message (#15).
* Make sure you have added the necessary tests for your changes.
* Run all the tests to assure nothing else was accidentally broken.
* Install and enable pre-commit_ (``pip install pre-commit``, then ``pre-commit
  install``) to ensure styleguides and codechecks are followed. CI will reject
  a change that does not conform to the guidelines.
* Don't forget to add yourself to AUTHORS_.

These guidelines also apply when helping with documentation (actually, for
typos and minor additions you might choose to `fork and edit`_).

.. _pre-commit: https://pre-commit.com/

Submitting Changes
------------------
* Push your changes to a topic branch in your fork of the repository.
* Submit a `Pull Request`_.
* Wait for maintainer feedback.

First time contributor?
-----------------------
It's alright. We've all been there.

Type annotations
----------------
There are two purposes for type annotations in the codebase: The first one is
to provide information about callables' signatures for applications such as
IDEs, so they can give useful hints within the client codebase when unexpected
types of values are passed to Cerberus' interfaces. The other is to document the
intended use of variables, such as ``bar = {}  # type: Dict[str, int]``.
Though testing type annotations with checkers like mypy_ can reveal possible
problems, this is not what they're intended for in this project. The annotations
however must be checked for correctness. As Python's typing system and the most
advanced type checker aren't mature yet and it isn't possible to annotate every
part correctly with a reasonable effort due to the nature of Cerberus
architecture, there has to be a compromise to comply with the afore mentioned
goals and requirement:

1. All parts of the public API (functions, methods, class properties) *must* be
   type annotated. It is okay to cast_ variables and instruct type checkers
   to ignore errors (``# type: ignore``). It should occasionally be checked
   whether these can be removed due to progress both within Cerberus' code
   and the used checker.

2. The annotation of code that is not supposed to be used directly is helpful
   for maintenance and *should* be added if the checker doesn't need to be
   pleased with the previously mentioned methods. If such are required,
   type annotations *must not* be added at all.

Don't know where to start?
--------------------------
There are usually several TODO comments scattered around the codebase, maybe
check them out and see if you have ideas and can help with them. Also, check
the `open issues`_ in case there's something that sparks your interest. What
about documentation? We're contributors and reviewers with different mother
tongues, so if you're fluent with it (or notice any error), why not help with
that? In any case, other than GitHub help_ pages, you might want to check this
excellent `Effective Guide to Pull Requests`_

.. _`the repository`: https://github.com/pyeve/cerberus
.. _AUTHORS: https://github.com/pyeve/cerberus/blob/master/AUTHORS
.. _`open issues`: https://github.com/pyeve/cerberus/issues
.. _`new issue`: https://github.com/pyeve/cerberus/issues/new
.. _Fork: https://help.github.com/articles/fork-a-repo
.. _`proper format`: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
.. _help: https://help.github.com/
.. _`Effective Guide to Pull Requests`: http://codeinthehole.com/writing/pull-requests-and-other-good-practices-for-teams-using-github/
.. _`fork and edit`: https://github.com/blog/844-forking-with-the-edit-button
.. _`Pull Request`: https://help.github.com/articles/creating-a-pull-request
.. _mypy: https://mypy.readthedocs.io/
.. _cast: https://docs.python.org/3/library/typing.html#typing.cast
