"""Exercise: raises / approx / warns.

make ex M=01
"""

from __future__ import annotations

import warnings

import pytest

from shop.domain.errors import InvalidOrderError, PaymentDeclinedError
from shop.domain.pricing import calculate_discount_cents


def charge(amount_cents: int) -> str:
    """A tiny stand-in payment call: declines anything over $1,000."""
    if amount_cents > 100_000:
        raise PaymentDeclinedError(reason="amount exceeds limit")
    return "pay_ok"


def test_charge_over_limit_raises_payment_declined() -> None:
    # TODO: use pytest.raises to assert charge(150_000) raises PaymentDeclinedError,
    # AND assert on the exception's `.reason` attribute (don't use match= for this
    # one -- practice the `as excinfo` form instead).
    with pytest.raises(PaymentDeclinedError) as excinfo:
        charge(150_000)

    assert excinfo.value.reason == "amount exceeds limit"


def test_discount_rate_as_a_percentage() -> None:
    """calculate_discount_cents(10_000) should apply the 10% tier (see
    src/shop/domain/pricing.py's DISCOUNT_TIERS). Compute the *effective rate* as a
    float (discount / subtotal) and assert it with pytest.approx -- this is a case
    where an int-cents calculation legitimately produces a float once you divide.
    """
    subtotal = 10_000
    discount = calculate_discount_cents(subtotal)

    effective_rate = discount / subtotal

    # TODO: assert effective_rate == pytest.approx(...) with the right expected value.
    assert effective_rate == pytest.approx(0.1)


def test_negative_subtotal_raises_invalid_order_error() -> None:
    # TODO: assert that calculate_discount_cents(-100) raises InvalidOrderError,
    # using match= this time (its message mentions "negative").
    with pytest.raises(InvalidOrderError, match="negative"):
        calculate_discount_cents(-100)


def _old_calculate_discount(subtotal_cents: int) -> int:
    warnings.warn(
        "_old_calculate_discount is deprecated, use calculate_discount_cents",
        DeprecationWarning,
        stacklevel=2,
    )
    return calculate_discount_cents(subtotal_cents)


def test_old_calculate_discount_warns() -> None:
    # TODO: use pytest.warns to assert calling _old_calculate_discount(10_000) warns
    # with a DeprecationWarning matching "deprecated".
    with pytest.warns(DeprecationWarning, match="deprecated"):
        _old_calculate_discount(100)
