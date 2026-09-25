"""Stacking @parametrize decorators multiplies: this produces 3 x 2 = 6 test runs.
Run with -v and count them.
"""

from __future__ import annotations

import pytest

from shop.domain.pricing import calculate_tax_cents


@pytest.mark.parametrize("taxable_cents", [0, 1_000, 9_999])
@pytest.mark.parametrize("tax_rate", [0.0, 0.10])
def test_tax_grid(tax_rate: float, taxable_cents: int) -> None:
    """Every (tax_rate, taxable_cents) combination -- appropriate here because tax
    rate and taxable amount really do vary independently, and we want the full
    cross product, not a hand-picked subset.

    Decorator order matters for argument order in the test id (closest-to-function
    decorator varies slowest), but NOT for which parameter fills which argument --
    that's always matched by name.
    """
    result = calculate_tax_cents(taxable_cents, tax_rate)

    if tax_rate == 0.0:
        assert result == 0
    else:
        assert result == round(taxable_cents * tax_rate)


@pytest.mark.parametrize("quantity", [1, 2, 3])
@pytest.mark.parametrize("unit_price_cents", [0, 500])
def test_line_total_grid(unit_price_cents: int, quantity: int) -> None:
    """A second stacked example. Notice this is 2 x 3 = 6 cases for something that
    could also have been six explicit tuples -- stacking is a convenience for a true
    cross product, not a rule to apply reflexively. If you find yourself excluding
    some combinations after the fact, that's a sign a single parametrize with
    explicit tuples (docs/03-what-to-test.md's decision-table technique) is the
    better fit than a cross product you then have to prune.
    """
    from shop.domain.models import OrderLine
    from shop.domain.pricing import calculate_subtotal_cents

    line = OrderLine(product_id=1, quantity=quantity, unit_price_cents=unit_price_cents)

    assert calculate_subtotal_cents([line]) == unit_price_cents * quantity
