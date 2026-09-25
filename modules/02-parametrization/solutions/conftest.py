from __future__ import annotations

import pytest

from shop.domain.models import OrderLine


@pytest.fixture
def cart(request: pytest.FixtureRequest) -> list[OrderLine]:
    return [
        OrderLine(product_id=i, quantity=quantity, unit_price_cents=unit_price_cents)
        for i, (quantity, unit_price_cents) in enumerate(request.param, start=1)
    ]
