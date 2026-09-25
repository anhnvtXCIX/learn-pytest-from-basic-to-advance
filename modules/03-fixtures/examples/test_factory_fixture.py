"""Factory-as-fixture: when a test needs several, slightly-different instances of
something, a fixture that returns one object isn't enough -- return a *callable*
instead, with sensible defaults and overridable fields.

This is the pattern module 11's `polyfactory`-based factories generalize and
auto-generate; understand it by hand first.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from shop.domain.models import Product


@pytest.fixture
def make_product() -> Callable[..., Product]:
    _next_id = iter(range(1, 1_000))

    def _make(
        *,
        sku: str = "WIDGET",
        name: str = "Widget",
        unit_price_cents: int = 1_000,
        stock_qty: int = 10,
    ) -> Product:
        return Product(
            id=next(_next_id),
            sku=sku,
            name=name,
            unit_price_cents=unit_price_cents,
            stock_qty=stock_qty,
        )

    return _make


def test_default_product_is_reasonable(make_product: Callable[..., Product]) -> None:
    product = make_product()

    assert product.sku == "WIDGET"
    assert product.stock_qty == 10


def test_override_only_the_field_the_test_cares_about(make_product: Callable[..., Product]) -> None:
    """The point of the pattern: this test only needs to say what's DIFFERENT about
    its product (out of stock), not repeat every other field -- a reader immediately
    knows `stock_qty=0` is the interesting part.
    """
    out_of_stock = make_product(stock_qty=0)

    assert out_of_stock.stock_qty == 0
    assert out_of_stock.sku == "WIDGET"  # everything else still gets a sane default


def test_building_several_related_products(make_product: Callable[..., Product]) -> None:
    cheap = make_product(sku="CHEAP", unit_price_cents=100)
    expensive = make_product(sku="EXPENSIVE", unit_price_cents=100_000)

    assert cheap.id != expensive.id  # each call is independent
    assert expensive.unit_price_cents > cheap.unit_price_cents
