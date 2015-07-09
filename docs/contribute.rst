.. include:: ../CONTRIBUTING.rst

Running the Tests
-----------------
Cerberus runs under Python 2.6, 2.7, Python 3.3, Python 3.4 and PyPy. Therefore tests
will be run in those four platforms in our `continuous integration server`_.

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

    # From the project folder
    $ tox -e py34

If you have a running Docker_-daemon running you can run tests from a container
that has the necessary interpreters installed and pass arguments to ``tox``:

.. code-block:: console

    $ ./run-docker-tests -x

Using Pytest
~~~~~~~~~~~~
You also choose to run the whole test suite using pytest_:

.. code-block:: console

    # Run the whole test suite
    $ py.test

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~
Each time code is pushed to the ``master``  branch
the whole test-suite is executed on Travis-CI. This is also the case for
pull-requests. When a pull request is submitted and the CI run fails two things
happen: a 'the build is broken' email is sent to the submitter; the request is
rejected.  The contributor can then fix the code, add one or more commits as
needed, and push again.

The CI will also run flake8 so make sure that your code complies to PEP8 before
submitting a pull request, or be prepared to be mail-spammed by CI.

Source Code
-----------
Source code is available at `GitHub
<https://github.com/nicolaiarocci/cerberus>`_.

.. _`continuous integration server`: https://travis-ci.org/nicolaiarocci/cerberus/
.. _Docker: https://www.docker.com
.. _pytest: http://pytest.org
.. _tox: http://tox.readthedocs.org/en/latest/
