Cerberus Installation
=====================

This part of the documentation covers the installation of Cerberus. The first
step to using any software package is getting it properly installed. Please
refer to one of the many established ways to work in project-specific virtual
environments, i.e. the `Virtual Environments and Packages`_ section of the
Pyton documentation.


Stable Version
--------------

Cerberus is on the PyPI_ so all you need to do is:

.. code-block:: console

    $ pip install cerberus


Development Version
-------------------

Obtain the source (either as source distribution from the PyPI, with ``git`` or
other means that the Github platform provides) and use the following command
in the source's root directory for an editable installation. Subsequent changes
to the source code will affect its following execution without re-installation.

.. code-block:: console

    $ pip install -e .


.. _GitHub Repository: https://github.com/pyeve/cerberus
.. _PyPI: https://pypi.org/project/Cerberus
.. _Virtual Environments and Packages: https://docs.python.org/3/tutorial/venv.html
