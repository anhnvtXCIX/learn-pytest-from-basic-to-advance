"""Reference solution for exercises/test_parametrize.py."""

from __future__ import annotations

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents, calculate_tax_cents


@pytest.mark.parametrize(
    "taxable_cents,tax_rate,expected_tax_cents",
    [
        (1_000, 0.0, 0),
        (1_000, 0.05, 50),
        (1_000, 0.20, 200),
    ],
    ids=["zero_rate", "five_percent", "twenty_percent"],
)
def test_tax_at_various_rates(taxable_cents: int, tax_rate: float, expected_tax_cents: int) -> None:
    assert calculate_tax_cents(taxable_cents, tax_rate) == expected_tax_cents


@pytest.mark.parametrize(
    "lines,expected_subtotal",
    [
        ([(1, 999)], 999),
        ([(5, 200)], 1_000),
        ([(2, 100), (3, 50)], 350),
    ],
    ids=["single_line_999", "single_line_x5", "two_lines"],
)
def test_write_your_own_parametrize_decorator(
    lines: list[tuple[int, int]], expected_subtotal: int
) -> None:
    order_lines = [
        OrderLine(product_id=i, quantity=quantity, unit_price_cents=unit_price_cents)
        for i, (quantity, unit_price_cents) in enumerate(lines, start=1)
    ]

    assert calculate_subtotal_cents(order_lines) == expected_subtotal


@pytest.mark.parametrize(
    "cart,expected_subtotal",
    [
        ([(1, 500)], 500),
        ([(2, 100), (1, 250)], 450),
    ],
    indirect=["cart"],
    ids=["single_line", "two_lines"],
)
def test_subtotal_via_indirect_cart_fixture(cart: list[OrderLine], expected_subtotal: int) -> None:
    assert calculate_subtotal_cents(cart) == expected_subtotal
