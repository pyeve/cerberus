Cerberus
========

.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is a validation tool for Python dictionaries.

It provides type checking and basic functionality out of the box and is
designed to be easily extensible. It serves as the foundation block for Eve
validation module.

Cerberus is ISC Licensed and is tested for Python 2.6 and 2.7.

::

    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True
    

Work in progress
