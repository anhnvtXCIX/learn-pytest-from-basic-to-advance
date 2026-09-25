"""Property-based tests on domain/pricing.py -- the invariants that should hold for
ANY valid input, not just the boundary cases module 02 hand-picked.
"""

from __future__ import annotations

from hypothesis import example, given
from hypothesis import strategies as st

from shop.domain.models import OrderLine
from shop.domain.pricing import (
    calculate_discount_cents,
    calculate_subtotal_cents,
    calculate_tax_cents,
    calculate_totals,
)

# A strategy for "a realistic, valid order": 1-10 lines, positive quantities,
# reasonable prices. Bounding the ranges keeps examples meaningful (an order with a
# billion-dollar line item doesn't teach us anything new) without weakening the
# properties being checked.
order_lines_strategy = st.lists(
    st.builds(
        OrderLine,
        product_id=st.integers(min_value=1, max_value=1_000),
        quantity=st.integers(min_value=1, max_value=100),
        unit_price_cents=st.integers(min_value=0, max_value=1_000_000),
    ),
    min_size=1,
    max_size=10,
)

subtotal_strategy = st.integers(min_value=0, max_value=10_000_000)
tax_rate_strategy = st.floats(min_value=0, max_value=0.5, allow_nan=False, allow_infinity=False)


@given(subtotal_strategy)
@example(0)  # explicitly pin the zero case
@example(4_999)  # just below the lowest discount tier
@example(5_000)  # exactly at the lowest discount tier
def test_discount_never_exceeds_subtotal(subtotal_cents: int) -> None:
    discount = calculate_discount_cents(subtotal_cents)

    assert 0 <= discount <= subtotal_cents


@given(subtotal_strategy, tax_rate_strategy)
def test_tax_is_never_negative(taxable_cents: int, tax_rate: float) -> None:
    assert calculate_tax_cents(taxable_cents, tax_rate) >= 0


@given(order_lines_strategy, tax_rate_strategy)
def test_totals_identity_always_holds(lines: list[OrderLine], tax_rate: float) -> None:
    """The core invariant: however the pieces are computed, they must always add
    back up. This is the property module 00's exercise asked you to check for ONE
    hand-picked example; Hypothesis checks it for hundreds of generated ones.
    """
    totals = calculate_totals(lines, tax_rate)

    assert totals.total_cents == totals.subtotal_cents - totals.discount_cents + totals.tax_cents
    assert 0 <= totals.discount_cents <= totals.subtotal_cents
    assert totals.tax_cents >= 0
    assert totals.total_cents >= 0


@given(order_lines_strategy)
def test_subtotal_is_monotonic_in_quantity(lines: list[OrderLine]) -> None:
    """Adding one more unit of the first line's product should never DECREASE the
    subtotal -- a property that would catch, for example, an accidental subtraction
    somewhere in the summation.
    """
    baseline = calculate_subtotal_cents(lines)

    lines_with_one_more = list(lines)
    first = lines_with_one_more[0]
    lines_with_one_more[0] = OrderLine(
        product_id=first.product_id,
        quantity=first.quantity + 1,
        unit_price_cents=first.unit_price_cents,
    )

    assert calculate_subtotal_cents(lines_with_one_more) >= baseline
