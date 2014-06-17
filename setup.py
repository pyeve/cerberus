#!/usr/bin/env python

from setuptools import setup, find_packages

DESCRIPTION = ("Extensible validation for Python dictionaries.")
LONG_DESCRIPTION = open('README.rst').read()
VERSION = __import__('cerberus').__version__

setup(
    name='Cerberus',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Nicola Iarocci',
    author_email='nicola@nicolaiarocci.com',
    url='http://github.com/nicolaiarocci/cerberus',
    license=open('LICENSE').read(),
    platforms=["any"],
    packages=find_packages(),
    include_package_data=True,
    test_suite="cerberus.tests",
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
