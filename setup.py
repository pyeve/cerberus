#!/usr/bin/env python

from setuptools import setup, find_packages
import sys

DESCRIPTION = ("Lightweight, extensible schema and data validation tool for "
               "Python dictionaries.")
LONG_DESCRIPTION = open('README.rst').read()
VERSION = __import__('cerberus').__version__

needs_pytest = set(('pytest', 'test', 'ptr')) & set(sys.argv)
setup_requires = ['pytest-runner'] if needs_pytest else []


setup(
    name='Cerberus',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Nicola Iarocci',
    author_email='nicola@nicolaiarocci.com',
    url='http://github.com/nicolaiarocci/cerberus',
    license='ISC',
    platforms=["any"],
    packages=find_packages(),
    include_package_data=True,
    setup_requires=setup_requires,
    tests_require=['pytest'],
    test_suite="cerberus.tests",
    install_requires=[],
    keywords=['validation', 'schema', 'dictionaries'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
