"""Overrides the `tax_rate` fixture from ../conftest.py for every test in this
directory. Same fixture name, closer to the test -- closer wins.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def tax_rate() -> float:
    return 0.20  # a "high-tax jurisdiction" scenario, overriding the outer 0.08
