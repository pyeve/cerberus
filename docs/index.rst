Welcome to Cerberus
===================

Cerberus is a lightweight and extensible data validation library for
Python.

    ``CERBERUS``, n. The watch-dog of Hades, whose duty it was to guard the
    entrance; everybody, sooner or later, had to go there, and nobody wanted to
    carry off the entrance.
    - *Ambrose Bierce, The Devil's Dictionary*

Cerberus provides type checking and other base functionality out of the box and
is designed to be easily extensible, allowing for easy custom validation. It
has no dependencies and is thoroughly tested from Python 2.6 up to 3.5, PyPy
and PyPy3.

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

Table of Contents
-----------------
.. toctree::

    Installation <install>
    Usage <usage>
    Validation Rules <validation-rules>
    Normalization Rules <normalization-rules>
    Errors & Error Handling <errors>
    Extending <customize>
    Contributing <contribute>
    API <api>
    FAQ <faq>
    changelog
    authors
    contact
    license

Copyright Notice
----------------
Cerberus is an open source project by `Nicola Iarocci
<http://nicolaiarocci.com>`_. See the original `LICENSE
<https://github.com/nicolaiarocci/cerberus/blob/master/LICENSE>`_ for more
information.
