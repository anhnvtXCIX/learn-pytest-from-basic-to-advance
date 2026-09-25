"""Exercise: parametrize, ids, indirect.

    make ex M=02
"""

from __future__ import annotations

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents


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
    # TODO: this decorator is already complete -- just write the assertion.
    raise NotImplementedError("write this test")


def test_write_your_own_parametrize_decorator() -> None:
    """TODO: this test currently has no decorator at all. Add a
    `@pytest.mark.parametrize` decorator above this function (you'll need to change
    the signature too) covering these three cases for `calculate_subtotal_cents`,
    with meaningful `ids`:

      - a single line: quantity=1, unit_price_cents=999   -> subtotal 999
      - a single line: quantity=5, unit_price_cents=200   -> subtotal 1000
      - two lines: (2, 100) and (3, 50)                    -> subtotal 350

    Build the OrderLine object(s) inside the test body from whatever parameters you
    chose to pass in.
    """
    raise NotImplementedError("add a parametrize decorator and implement this test")


@pytest.mark.parametrize(
    "cart,expected_subtotal",
    [
        # TODO: add at least two (cart, expected_subtotal) cases here. `cart` is a
        # list of (quantity, unit_price_cents) tuples -- it goes through the `cart`
        # fixture in conftest.py before this test sees it (that's what indirect does).
    ],
    indirect=["cart"],
)
def test_subtotal_via_indirect_cart_fixture(cart: list[OrderLine], expected_subtotal: int) -> None:
    assert calculate_subtotal_cents(cart) == expected_subtotal
