"""Indirect parametrization: `cart`'s values go through the `cart` fixture in
conftest.py (which builds OrderLine objects) before the test sees them, instead of
landing in the test function directly.

`indirect=["cart"]` -- a list, not `True` -- makes only `cart` indirect while
`expected_subtotal` stays a plain, direct parameter. This is the usual real-world
shape: one or two "needs construction" parameters, plus plain expected-value ones.
"""

from __future__ import annotations

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents


@pytest.mark.parametrize(
    "cart,expected_subtotal",
    [
        ([(2, 500)], 1_000),
        ([(1, 100), (3, 200)], 700),
        ([(1, 100), (3, 200), (2, 50)], 800),
    ],
    indirect=["cart"],
    ids=["single_line", "two_lines", "three_lines"],
)
def test_subtotal_from_cart_fixture(cart: list[OrderLine], expected_subtotal: int) -> None:
    assert calculate_subtotal_cents(cart) == expected_subtotal
