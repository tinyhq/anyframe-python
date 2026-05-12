"""Smoke test that the package imports and exposes a version."""

import re

import anyframe


def test_version_is_semver():
    """__version__ is a semver string."""
    assert re.match(r"^\d+\.\d+\.\d+", anyframe.__version__), anyframe.__version__
