#!/usr/bin/env python

from setuptools import setup, find_packages
import sys

DESCRIPTION = (
    "Lightweight, extensible schema and data validation tool for "
    "Python dictionaries."
)
LONG_DESCRIPTION = open("README.rst").read()
VERSION = "1.3"

setup_requires = (
    ["pytest-runner"] if any(x in sys.argv for x in ("pytest", "test", "ptr")) else []
)


setup(
    name="Cerberus",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author="Nicola Iarocci",
    author_email="nicola@nicolaiarocci.com",
    url="http://docs.python-cerberus.org",
    license="ISC",
    platforms=["any"],
    packages=find_packages(),
    include_package_data=True,
    setup_requires=setup_requires,
    tests_require=["pytest"],
    test_suite="cerberus.tests",
    install_requires=[],
    keywords=["validation", "schema", "dictionaries", "documents", "normalization"],
    python_requires=">=2.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
