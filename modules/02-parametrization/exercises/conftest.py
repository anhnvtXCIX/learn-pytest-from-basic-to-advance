from __future__ import annotations

import pytest

from shop.domain.models import OrderLine


@pytest.fixture
def cart(request: pytest.FixtureRequest) -> list[OrderLine]:
    """Same shape as examples/conftest.py's `cart` fixture -- reimplemented here
    because exercises/ and examples/ are separate conftest.py scopes. See module 13
    for why fixtures like this eventually move into a shared `testkit` package
    instead of being copied per module.
    """
    return [
        OrderLine(product_id=i, quantity=quantity, unit_price_cents=unit_price_cents)
        for i, (quantity, unit_price_cents) in enumerate(request.param, start=1)
    ]
