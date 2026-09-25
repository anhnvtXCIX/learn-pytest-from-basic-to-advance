"""A first look at pytest: no classes, no boilerplate, just functions and `assert`.

Run these with the flags from the module README and watch what changes:
    uv run pytest modules/00-getting-started/examples -v
    uv run pytest modules/00-getting-started/examples -k discount
    uv run pytest modules/00-getting-started/examples -m slow
    uv run pytest modules/00-getting-started/examples --durations=5
"""

from __future__ import annotations

import time

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_discount_cents, calculate_subtotal_cents


def test_subtotal_is_price_times_quantity() -> None:
    lines = [OrderLine(product_id=1, quantity=3, unit_price_cents=500)]

    subtotal = calculate_subtotal_cents(lines)

    assert subtotal == 1500


def test_subtotal_sums_multiple_lines() -> None:
    lines = [
        OrderLine(product_id=1, quantity=2, unit_price_cents=500),
        OrderLine(product_id=2, quantity=1, unit_price_cents=999),
    ]

    subtotal = calculate_subtotal_cents(lines)

    assert subtotal == 1999


def test_try_breaking_this_to_see_assertion_introspection() -> None:
    """This test passes as written. Change the `1500` below to `1600` and rerun with
    `-vv`: pytest shows you `assert 1500 == 1600`, not just "assertion failed" --
    that's assertion rewriting, and it's why you almost never need a helper method
    like `assertEqual`.
    """
    lines = [OrderLine(product_id=1, quantity=3, unit_price_cents=500)]

    subtotal = calculate_subtotal_cents(lines)

    assert subtotal == 1500


def test_no_discount_below_the_lowest_tier() -> None:
    assert calculate_discount_cents(4_999) == 0


def test_discount_at_the_lowest_tier_boundary() -> None:
    assert calculate_discount_cents(5_000) == 250  # 5% of 5000


@pytest.mark.slow
def test_this_one_is_deliberately_slow() -> None:
    """Marked `slow` so `-m "not slow"` can exclude it, and so `--durations` has
    something obvious to point at. It isn't testing anything real -- it's here so
    module 00 has something to filter.
    """
    time.sleep(0.3)
    assert calculate_subtotal_cents([OrderLine(1, 1, 100)]) == 100
