# -*- coding: utf-8 -*-

from decimal import Decimal

from pytest import mark

from cerberus import TypeDefinition, Validator
from cerberus.tests import assert_fail, assert_success
from cerberus.utils import validator_factory
from cerberus.validator import BareValidator
from cerberus.platform import PYTHON_VERSION, importlib_metadata


if PYTHON_VERSION > 3 and PYTHON_VERSION < 3.4:
    from imp import reload
elif PYTHON_VERSION >= 3.4:
    from importlib import reload
else:
    pass  # Python 2.x


def test_pkgresources_version(monkeypatch):
    def return_fake_version(name):
        assert name == "Cerberus"
        return "1.2.3"

    with monkeypatch.context() as m:
        cerberus = __import__("cerberus")
        m.setattr("cerberus.importlib_metadata.version", return_fake_version)
        reload(cerberus)
        assert cerberus.__version__ == "1.2.3"


def test_version_not_found(monkeypatch):
    def raise_package_not_found_error(name):
        assert name == "Cerberus"
        raise importlib_metadata.PackageNotFoundError

    with monkeypatch.context() as m:
        cerberus = __import__("cerberus")
        m.setattr("cerberus.importlib_metadata.version", raise_package_not_found_error)
        reload(cerberus)
        assert cerberus.__version__ == "unknown"


def test_clear_cache(validator):
    assert len(validator._valid_schemas) > 0
    validator.clear_caches()
    assert len(validator._valid_schemas) == 0


def test_docstring(validator):
    assert validator.__doc__


# Test that testing with the sample schema works as expected
# as there might be rules with side-effects in it


@mark.parametrize(
    "test,document",
    ((assert_fail, {"an_integer": 60}), (assert_success, {"an_integer": 110})),
)
def test_that_test_fails(test, document):
    try:
        test(document)
    except AssertionError:
        pass
    else:
        raise AssertionError("test didn't fail")


def test_dynamic_types():
    decimal_type = TypeDefinition("decimal", (Decimal,), ())
    document = {"measurement": Decimal(0)}
    schema = {"measurement": {"type": "decimal"}}

    validator = Validator()
    validator.types_mapping["decimal"] = decimal_type
    assert_success(document, schema, validator)

    class MyValidator(Validator):
        types_mapping = Validator.types_mapping.copy()
        types_mapping["decimal"] = decimal_type

    validator = MyValidator()
    assert_success(document, schema, validator)


def test_mro():
    assert Validator.__mro__ == (Validator, BareValidator, object), Validator.__mro__


def test_mixin_init():
    class Mixin(object):
        def __init__(self, *args, **kwargs):
            kwargs["test"] = True
            super(Mixin, self).__init__(*args, **kwargs)

    MyValidator = validator_factory("MyValidator", Mixin)
    validator = MyValidator()
    assert validator._config["test"]


def test_sub_init():
    class MyValidator(Validator):
        def __init__(self, *args, **kwargs):
            kwargs["test"] = True
            super(MyValidator, self).__init__(*args, **kwargs)

    validator = MyValidator()
    assert validator._config["test"]
