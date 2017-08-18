.. include:: ../CONTRIBUTING.rst

Running the Tests
-----------------
Cerberus runs under Python 2.6, 2.7, 3.3, 3.4, 3.5, PyPy and PyPy3. Therefore
tests will be run in those four platforms in our `continuous integration
server`_.

The easiest way to get started is to run the tests in your local environment
with:

.. code-block:: console

   $ python setup.py test

Testing with other Python versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before you submit a pull request, make sure your tests and changes run in
all supported python versions: 2.6, 2.7, 3.3, 3.4 and PyPy. Instead of creating all
those environments by hand, Cerberus uses tox_.

Make sure you have all required python versions installed and run:

.. code-block:: console

   $ pip install tox  # First time only
   $ tox

This might take some time the first run as the different virtual environments
are created and dependencies are installed. If everything is ok, you will see
the following:

.. code-block:: console

    _________ summary _________
    py26: commands succeeded
    py27: commands succeeded
    py33: commands succeeded
    py34: commands succeeded
    pypy: commands succeeded
    flake8: commands succeeded
    congratulations :)

If something goes **wrong** and one test fails, you might need to run that test
in the specific python version. You can use the created environments to run
some specific tests. For example, if a test suite fails in Python 3.4:

.. code-block:: console

    $ # From the project folder
    $ tox -e py34

Have a look at ``/tox.ini`` for the available test environments and their workings.

Using Pytest
~~~~~~~~~~~~
You also choose to run the whole test suite using pytest_:

.. code-block:: console

    $ # Run the whole test suite
    $ py.test

Using Docker
~~~~~~~~~~~~

If you have a running Docker_-daemon running you can run tests from a container
that has the necessary interpreters and packages installed and pass arguments
to ``tox``:

.. code-block:: console

    $ # in the project's root directory
    $ ./run-docker-tests -e pypy3 -e doctest

You can run the script without any arguments to test the project exactly as
`Continuous Integration`_ does without having to setup anything.
If there's a directoy ``.tox`` in the project-folder it will be used to store
and access cached virtual environments and test-logs.

Building the HTML-documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To preview the rendered HTML-documentation you must intially install the
documentation framework and a theme:

.. code-block:: console

    $ # in the project's root directory
    $ pip install -r requirements-docs.txt

The HTML build is triggered with:

.. code-block:: console

    $ # in 'docs'-folder
    $ make html

The result can be accessed by opening ``docs/_build/html/index.html``.

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~
Each time code is pushed to the ``master``  branch the whole test-suite is
executed on Travis-CI_.
This is also the case for pull-requests. A box at the bottom of its
conversation-view will inform about the tests' status.
The contributor can then fix the code, add commits, squash_ the commits and
push again.
The CI will also run flake8_ so make sure that your code complies to PEP8 and
test links and sample-code in the documentation.

Source Code
-----------
Source code is available at `GitHub
<https://github.com/pyeve/cerberus>`_.

.. _`continuous integration server`: https://travis-ci.org/pyeve/cerberus/
.. _Docker: https://www.docker.com
.. _flake8: https://flake8.readthedocs.org
.. _pytest: https://pytest.org
.. _squash: http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html
.. _tox: https://tox.readthedocs.io
.. _Travis-CI: https://travis-ci.org
