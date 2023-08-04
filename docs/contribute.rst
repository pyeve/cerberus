How to Contribute
=================

There are no plans to develop Cerberus further than the current feature set.
Bug fixes and documentation improvements are welcome and will be published with
yearly service releases.


Making Changes
--------------
* Fork_ the repository_ on GitHub.
* Create a new topic branch from the ``1.3.x`` branch.
* Make commits of logical units (if needed rebase your feature branch before
  submitting it).
* Make sure your commit messages are in the `proper format`_.
* If your commit fixes an open issue, reference it in the commit message.
* Make sure you have added the necessary tests for your changes.
* Run all the tests to assure nothing else was accidentally broken.
* Install and enable pre-commit_ (``pip install pre-commit``, then ``pre-commit
  install``) to ensure styleguides and codechecks are followed.
* Don't forget to add yourself to the ``AUTHORS.rst`` document.

These guidelines also apply when helping with documentation (actually, for
typos and minor additions you might choose to `fork and edit`_).


Submitting Changes
------------------
* Push your changes to the topic branch in your fork of the repository.
* Submit a `Pull Request`_.
* Wait for maintainer feedback. Please be patient.


Running the Tests
-----------------

The easiest way to get started is to run the tests in your local environment
with pytest_:

.. code-block:: console

   $ pytest cerberus/tests


Testing with other Python versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you submit a pull request, make sure your tests and changes run in
all supported python versions. Instead of creating all those environments by
hand, you can use tox_ that automatically manages virtual environments. Mind
that the interpreters themselves need to be available on the system.

.. code-block:: console

   $ pip install tox  # First time only
   $ tox

This might take some time the first run as the different virtual environments
are created and dependencies are installed.

If something goes wrong and one test fails, you might need to run that test in
the specific python version. You can use the created environments to run some
specific tests. For example, if a test suite fails in Python 3.11:

.. code-block:: console

    $ tox -e py311

Have a look at ``tox.ini`` for the available test environments and their setup.


Running the benchmarks
~~~~~~~~~~~~~~~~~~~~~~

There's a benchmark suite that you can use to measure how changes imapact
Cerberus' performance:

.. code-block:: console

    $ pytest cerberus/benchmarks


Building the HTML-documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To preview the rendered HTML-documentation you must initially install the
documentation framework and a theme:

.. code-block:: console

    $ pip install -r docs/requirements.txt

The HTML build is triggered with:

.. code-block:: console

    $ make -C docs html

The result can be accessed by opening ``docs/_build/html/index.html``.


.. _Fork: https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo
.. _`fork and edit`: https://github.blog/2011-04-26-forking-with-the-edit-button/
.. _pre-commit: https://pre-commit.com/
.. _`proper format`: https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
.. _`Pull Request`: https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request
.. _pytest: https://pytest.org
.. _repository: https://github.com/pyeve/cerberus
.. _tox: https://tox.readthedocs.io
