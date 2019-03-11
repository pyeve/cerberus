# -*- coding: utf-8 -*-

import cerberus


def test_pkgresources_version(get_distribution_finds_distribution):
    version = cerberus.__version__
    assert version == '1.2.3'


def test_missing_version(get_distribution_raises_exception):
    version = cerberus.__version__
    assert version == 'unknown'
