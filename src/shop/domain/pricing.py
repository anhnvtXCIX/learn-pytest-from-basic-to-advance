"""Pure pricing logic: no I/O, no clock, no randomness.

This module is the best place in the whole repo to *start* testing, and the best
place to come back to once you've learned parametrize (module 02) and Hypothesis
(module 12): every function here is a pure function of its inputs, so there is no
excuse not to test it exhaustively.

Money is handled as integer cents throughout. Never use `float` for money: floats
can't represent most decimal fractions exactly (`0.1 + 0.2 != 0.3`), which silently
corrupts totals in ways that are miserable to test for and miserable to debug in
production. We use `Decimal` only at the rounding boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from shop.domain.errors import InvalidOrderError
from shop.domain.models import OrderLine, OrderTotals

# (minimum subtotal in cents, discount rate) -- first matching tier wins, checked
# highest threshold first. A $250+ order gets 15% off, $100+ gets 10%, $50+ gets 5%.
DISCOUNT_TIERS: tuple[tuple[int, Decimal], ...] = (
    (25_000, Decimal("0.15")),
    (10_000, Decimal("0.10")),
    (5_000, Decimal("0.05")),
)


def _round_cents(amount: Decimal) -> int:
    """Round to the nearest cent, ties away from zero.

    This is a deliberate, documented choice (not "whatever the language does by
    default") specifically so that tests can assert on it. Python's own `round()`
    uses banker's rounding (round-half-to-even), which surprises almost everyone the
    first time a test fails on a `.5` boundary -- that surprise is itself a small
    lesson in why "round" isn't as pure a concept as it sounds.
    """
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_subtotal_cents(lines: Sequence[OrderLine]) -> int:
    """Sum of line totals. Raises InvalidOrderError for structurally bad input."""
    if not lines:
        raise InvalidOrderError("an order must have at least one line")
    for line in lines:
        if line.quantity <= 0:
            raise InvalidOrderError(
                f"quantity must be positive, got {line.quantity} for product {line.product_id}"
            )
        if line.unit_price_cents < 0:
            raise InvalidOrderError(
                f"unit_price_cents must not be negative, got {line.unit_price_cents} "
                f"for product {line.product_id}"
            )
    return sum(line.line_total_cents for line in lines)


def calculate_discount_cents(subtotal_cents: int) -> int:
    """Volume discount based on subtotal. Returns 0 below the lowest tier."""
    if subtotal_cents < 0:
        raise InvalidOrderError(f"subtotal_cents must not be negative, got {subtotal_cents}")
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal_cents >= threshold:
            return _round_cents(Decimal(subtotal_cents) * rate)
    return 0


def calculate_tax_cents(taxable_cents: int, tax_rate: float) -> int:
    """Tax on the post-discount amount."""
    if taxable_cents < 0:
        raise InvalidOrderError(f"taxable_cents must not be negative, got {taxable_cents}")
    if tax_rate < 0:
        raise InvalidOrderError(f"tax_rate must not be negative, got {tax_rate}")
    return _round_cents(Decimal(taxable_cents) * Decimal(str(tax_rate)))


def calculate_totals(lines: Sequence[OrderLine], tax_rate: float) -> OrderTotals:
    """The one function callers actually use; the others exist to be tested in isolation."""
    subtotal = calculate_subtotal_cents(lines)
    discount = calculate_discount_cents(subtotal)
    taxable = subtotal - discount
    tax = calculate_tax_cents(taxable, tax_rate)
    total = taxable + tax
    return OrderTotals(
        subtotal_cents=subtotal,
        discount_cents=discount,
        tax_cents=tax,
        total_cents=total,
    )
