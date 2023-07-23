Frequently Asked Questions
==========================

Can I use Cerberus to validate objects?
---------------------------------------

Yes. See `Validating user objects with Cerberus <https://nicolaiarocci.com/validating-user-objects-cerberus/>`_.

Are Cerberus validators thread-safe, can they be used in different threads?
---------------------------------------------------------------------------

The normalization and validation methods of validators make a copy of the
provided document and store it as :attr:`~cerberus.Validator.document`
property. Because of this it is advised to create a new
:class:`~cerberus.Validator` instance for each processed document when used in
a multi-threaded context. Alternatively you can use a
:class:`py3:threading.Lock` to confirm that only one document processing is
running at any given time.
