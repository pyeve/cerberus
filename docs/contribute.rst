.. include:: ../CONTRIBUTING.rst

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

If something goes **wrong** and one test fails, you might need to run that test
in the specific python version. You can use the created environments to run
some specific tests. For example, if a test suite fails in Python 3.11:

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

Source Code
-----------

Source code is available at `GitHub <https://github.com/pyeve/cerberus>`_.

.. _pytest: https://pytest.org
.. _tox: https://tox.readthedocs.io
