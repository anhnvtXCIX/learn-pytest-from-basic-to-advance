"""Basic parametrize: ids, and pytest.param() for a marked case."""

from __future__ import annotations

import pytest

from shop.domain.pricing import calculate_discount_cents


@pytest.mark.parametrize(
    "subtotal_cents,expected_discount_cents",
    [
        (0, 0),
        (4_999, 0),
        (5_000, 250),  # 5% tier boundary
        (9_999, 500),
        (10_000, 1_000),  # 10% tier boundary
        (24_999, 2_500),
        (25_000, 3_750),  # 15% tier boundary
        (100_000, 15_000),
    ],
    ids=[
        "zero",
        "just_below_5pct_tier",
        "at_5pct_tier_boundary",
        "just_below_10pct_tier",
        "at_10pct_tier_boundary",
        "just_below_15pct_tier",
        "at_15pct_tier_boundary",
        "well_above_highest_tier",
    ],
)
def test_discount_tiers(subtotal_cents: int, expected_discount_cents: int) -> None:
    assert calculate_discount_cents(subtotal_cents) == expected_discount_cents


@pytest.mark.parametrize(
    "subtotal_cents",
    [
        pytest.param(-1, id="barely_negative"),
        pytest.param(-1_000_000, id="very_negative"),
    ],
)
def test_negative_subtotal_is_invalid(subtotal_cents: int) -> None:
    """`pytest.param(..., id=...)` is the per-case way to set an id, as an
    alternative to the decorator-level `ids=[...]` list used above -- reach for
    this form when only some cases need a custom id, or (as in module 04) when a
    case also needs its own `marks=`.
    """
    from shop.domain.errors import InvalidOrderError

    with pytest.raises(InvalidOrderError):
        calculate_discount_cents(subtotal_cents)
