"""Custom markers, and the -m override-not-AND behavior described in the README.

Try:
    uv run pytest modules/04-markers-and-config/examples/test_marker_selection.py -m unit -v
    uv run pytest modules/04-markers-and-config/examples/test_marker_selection.py -m "not slow" -v
"""

from __future__ import annotations

import time

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents


@pytest.mark.unit
def test_marked_unit() -> None:
    assert calculate_subtotal_cents([OrderLine(1, 1, 100)]) == 100


@pytest.mark.unit
@pytest.mark.slow
def test_marked_unit_and_slow() -> None:
    """A test can carry more than one marker -- stack the decorators."""
    time.sleep(0.1)
    assert calculate_subtotal_cents([OrderLine(1, 2, 100)]) == 200
