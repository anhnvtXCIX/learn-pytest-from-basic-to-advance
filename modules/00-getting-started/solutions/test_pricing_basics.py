"""Reference solution for exercises/test_pricing_basics.py. Diff your attempt
against this -- don't just replace it.
"""

from __future__ import annotations

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents, calculate_tax_cents, calculate_totals


def test_subtotal_of_a_single_line() -> None:
    lines = [OrderLine(product_id=1, quantity=4, unit_price_cents=250)]

    subtotal = calculate_subtotal_cents(lines)

    assert subtotal == 1_000  # 4 * 250


def test_tax_is_a_percentage_of_the_taxable_amount() -> None:
    tax = calculate_tax_cents(1_000, 0.10)

    assert tax == 100


def test_totals_add_up() -> None:
    lines = [OrderLine(product_id=1, quantity=2, unit_price_cents=1_000)]  # 2000, below all tiers

    totals = calculate_totals(lines, tax_rate=0.10)

    assert totals.total_cents == totals.subtotal_cents - totals.discount_cents + totals.tax_cents
    # and, since this order is below the lowest discount tier:
    assert totals.discount_cents == 0
    assert totals.subtotal_cents == 2_000
    assert totals.tax_cents == 200
    assert totals.total_cents == 2_200
