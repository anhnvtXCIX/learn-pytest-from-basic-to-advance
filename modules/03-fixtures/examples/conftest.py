"""Fixtures shared by every test in modules/03-fixtures/examples/ (and, unless
overridden, everything below it -- see nested/conftest.py).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def tax_rate() -> float:
    """The 'outer' tax_rate fixture. nested/conftest.py defines one with the same
    name that wins for tests inside nested/ -- see nested/test_override.py.
    """
    return 0.08
