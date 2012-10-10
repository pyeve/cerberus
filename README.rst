Cerberus
========

.. image:: https://secure.travis-ci.org/nicolaiarocci/cerberus.png?branch=master 
        :target: https://secure.travis-ci.org/nicolaiarocci/cerberus

Cerberus is a Python dictionay validation tool. It provides type checking
and basic functionality out of the box, and is designed to be easily
extensible. In fact, it serves as the foundation of Eve's validation module.

Cerberus is ISC Licensed (use it freely) and is currently tested for Python 2.6
and 2.7.

::
    >>> v = Validator({'name': {'type': 'string'}})
    >>> v.validate({'name': 'john doe'})
    True
    

Work in progress
