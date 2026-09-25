"""Fixture + hook supporting this module's indirect-parametrization and
pytest_generate_tests examples. Scoped to this directory only (see module 03 on
conftest.py layering).
"""

from __future__ import annotations

import pytest

from shop.domain.models import OrderLine
from shop.domain.pricing import DISCOUNT_TIERS


@pytest.fixture
def cart(request: pytest.FixtureRequest) -> list[OrderLine]:
    """Indirect fixture: `request.param` is a list of (quantity, unit_price_cents)
    tuples. See test_parametrize_indirect.py -- this exists because *building* the
    OrderLine objects is enough boilerplate that hiding it behind a fixture makes the
    parametrize table read as pure data, not construction code.
    """
    return [
        OrderLine(product_id=i, quantity=quantity, unit_price_cents=unit_price_cents)
        for i, (quantity, unit_price_cents) in enumerate(request.param, start=1)
    ]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate one parametrize case per entry in DISCOUNT_TIERS, read from the real
    table in src/shop/domain/pricing.py -- not copy-pasted. If someone adds a fourth
    tier, this test automatically gains a fourth case; a hand-written parametrize
    list wouldn't. See test_generated_boundaries.py.
    """
    if {"tier_threshold_cents", "tier_rate"} <= set(metafunc.fixturenames):
        cases = [(threshold, float(rate)) for threshold, rate in DISCOUNT_TIERS]
        ids = [f"{float(rate):.0%}_tier" for _, rate in DISCOUNT_TIERS]
        metafunc.parametrize("tier_threshold_cents,tier_rate", cases, ids=ids)
