"""Exercise: fill in each TODO so the test passes.

Run just this file's exercises with:
    make ex M=00

Don't look at solutions/test_pricing_basics.py until you're green (or truly stuck).
"""

from __future__ import annotations

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents, calculate_tax_cents, calculate_totals


def test_subtotal_of_a_single_line() -> None:
    """A single line: 4 units at 250 cents each."""
    lines = [OrderLine(product_id=1, quantity=4, unit_price_cents=250)]

    subtotal = calculate_subtotal_cents(lines)

    assert subtotal == 1000


def test_tax_is_a_percentage_of_the_taxable_amount() -> None:
    """calculate_tax_cents(taxable_cents, tax_rate) -- tax_rate is a fraction, e.g.
    0.10 for 10%. Read the function's docstring in src/shop/domain/pricing.py, then
    fill in a call and an assertion for "1000 cents taxed at 10%".
    """
    tax_cents = calculate_tax_cents(taxable_cents=2000, tax_rate=0.05)

    assert tax_cents == 100


def test_totals_add_up() -> None:
    """calculate_totals returns an OrderTotals. For ANY valid input (this is the
    invariant module 12 will later check with Hypothesis across hundreds of inputs --
    for now, just confirm it holds for one example you construct yourself):

        total_cents == subtotal_cents - discount_cents + tax_cents

    Build a small order (pick quantities/prices below the lowest discount tier so you
    don't also have to hand-compute a discount), call calculate_totals, and assert
    the identity above using the fields on the returned OrderTotals.
    """
    lines = [
        OrderLine(product_id=1, quantity=2, unit_price_cents=1200),
        OrderLine(product_id=2, quantity=1, unit_price_cents=2000),
    ]

    order_totals = calculate_totals(lines=lines, tax_rate=0.10)

    assert order_totals.total_cents == 4840
    assert order_totals.tax_cents == 440
    assert order_totals.discount_cents == 0
    assert order_totals.subtotal_cents == 4400
