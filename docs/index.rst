Welcome to Cerberus
===================

    ``CERBERUS``, n. The watch-dog of Hades, whose duty it was to guard the
    entrance; everybody, sooner or later, had to go there, and nobody wanted to
    carry off the entrance.
    - *Ambrose Bierce, The Devil's Dictionary*

Cerberus provides powerful yet simple and lightweight data validation
functionality out of the box and is designed to be easily extensible, allowing
for custom validation. It has no dependencies and is thoroughly tested
from Python 2.6 up to 3.5, PyPy and PyPy3.

At a Glance
-----------
You define a validation schema and pass it to an instance of the
:class:`~cerberus.Validator` class: ::

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

Then you simply invoke the :meth:`~cerberus.Validator.validate` to validate
a dictionary against the schema. If validation succeeds, ``True`` is returned:

::

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True

Funding Cerberus
----------------
Cerberus is a :doc:`collaboratively funded project <funding>`. If you run
a business and are using Cerberus in a revenue-generating product, it would
make business sense to sponsor its development: it ensures the project that
your product relies on stays healthy and actively maintained. 

Individual users are also welcome to make either a recurring pledge or a one
time donation if Cerberus has helped you in your work or personal projects.
Every single sign-up makes a significant impact towards making Cerberus
possible. 

To join the backer ranks, check out `Cerberus campaign on Patreon`_.

Table of Contents
-----------------
.. toctree::

    Installation <install>
    Usage <usage>
    schemas
    validation-rules
    normalization-rules
    errors
    Extending <customize>
    Contributing <contribute>
    Funding <funding>
    API <api>
    FAQ <faq>
    changelog
    upgrading
    authors
    contact
    license

Copyright Notice
----------------
Cerberus is an open source project by `Nicola Iarocci
<http://nicolaiarocci.com>`_. See the original `LICENSE
<https://github.com/pyeve/cerberus/blob/master/LICENSE>`_ for more
information.

.. _`Cerberus campaign on Patreon`: https://www.patreon.com/nicolaiarocci
