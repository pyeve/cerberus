External resources
==================

Here are some recommended resources that deal with Cerberus.
If you find something interesting on the web, please amend it to this document
and open a pull request (see :doc:`contribute`).


7 Best Python Libraries For Validating Data (February 2018)
-----------------------------------------------------------

`Clickbait <https://www.yeahhub.com/7-best-python-libraries-validating-data/>`_
that mentions Cerberus. It's a starting point to compare libraries with a
similar scope though.

Nicola Iarocci: Cerberus, or Data Validation for Humans (November 2017)
-----------------------------------------------------------------------

Get fastened for the full tour on Cerberus that Nicola gave in a
`talk <https://www.youtube.com/watch?v=vlHAjIPvoT4>`_ at PiterPy 2017.
No bit is missed, so don't miss it!
The talk also includes a sample of the actual pronunciation of Iarocci as
extra takeaway.

Henry Ölsner: Validate JSON data using cerberus (March 2016)
------------------------------------------------------------

In this `blog post <https://codingnetworker.com/2016/03/validate-json-data-using-cerberus/>`_
the author describes how to validate network configurations with a schema noted
in YAML. The article that doesn't spare on code snippets develops the
resulting schema by gradually increasing its complexity. A custom type check is
also implemented, but be aware that version *0.9.2* is used. With 1.0 and later
the implementation should look like this:

.. code-block:: python

    def _validate_type_ipv4address(self, value):
        try:
            ipaddress.IPv4Address(value)
        except:
            return False
        else:
            return True
