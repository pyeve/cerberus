Frequently Asked Questions
==========================

Can I use Cerberus to validate objects?
---------------------------------------

Yes. See `Validating user objects with Cerberus <https://nicolaiarocci.com/validating-user-objects-cerberus/>`_.

Are Cerberus validators thread-safe, can they be used in different threads?
---------------------------------------------------------------------------

The `validate*` methods of Cerberus validators make a copy of the document
being validated and store it internally. Because of this it is advised to
create a new validator object for each document you will be validating when
used in a multi-threaded context. Alternatively you can use a `threading.Lock`
to confirm that only one `validate` (or `validated`) call is running at any
given time.
