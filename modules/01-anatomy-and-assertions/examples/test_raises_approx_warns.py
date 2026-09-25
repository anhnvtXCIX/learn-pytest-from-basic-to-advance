"""pytest.raises, pytest.approx, pytest.warns -- worked examples against real
exceptions and real (if slightly contrived) float/warning cases.
"""

from __future__ import annotations

import warnings

import pytest

from shop.domain.errors import InsufficientStockError, InvalidOrderError
from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents


def reserve(available: int, requested: int) -> None:
    """A tiny stand-in for what `ProductRepository.reserve_stock` checks, kept local
    so this module doesn't need a database -- see module 09 for the real thing.
    """
    if requested > available:
        raise InsufficientStockError(product_id=42, requested=requested, available=available)


def test_raises_checks_the_type() -> None:
    with pytest.raises(InsufficientStockError):
        reserve(available=1, requested=5)


def test_raises_with_match_checks_the_message() -> None:
    # match= is a regex searched (not fully matched) against str(exception).
    with pytest.raises(InsufficientStockError, match=r"only 1 in stock"):
        reserve(available=1, requested=5)


def test_raises_and_inspect_attributes() -> None:
    """Prefer this over `match=` when the exception carries structured data --
    attributes are part of the contract; the message is prose.
    """
    with pytest.raises(InsufficientStockError) as excinfo:
        reserve(available=1, requested=5)

    assert excinfo.value.product_id == 42
    assert excinfo.value.requested == 5
    assert excinfo.value.available == 1


def test_the_block_should_contain_only_the_call_under_test() -> None:
    """Anti-pattern to notice: if the `with` block contained three calls, a failure
    wouldn't tell you which one raised. Keep arrange/act separate.
    """
    lines = [OrderLine(product_id=1, quantity=1, unit_price_cents=100)]  # Arrange

    with pytest.raises(InvalidOrderError):
        calculate_subtotal_cents([])  # Act -- the ONE call we're asserting on

    # A second, unrelated assertion belongs in its own test, not bolted on here.
    assert calculate_subtotal_cents(lines) == 100


def test_approx_for_a_genuine_float_comparison() -> None:
    """Money in this repo is integer cents specifically to avoid needing `approx`
    for money math (see domain/pricing.py's docstring). Here's a case that
    legitimately produces a float: displaying tax as a percentage.
    """
    tax_rate = 0.08
    display_percentage = tax_rate * 100

    assert display_percentage == pytest.approx(8.0)

    # Without approx, this kind of comparison is exactly why: 0.1 + 0.2 != 0.3
    assert 0.1 + 0.2 != 0.3  # demonstrates the problem approx solves
    assert pytest.approx(0.3) == 0.1 + 0.2


def test_approx_with_explicit_tolerance() -> None:
    measured = 99.94
    assert measured == pytest.approx(100.0, rel=0.001)  # within 0.1%


def _load_settings_v1(payload: dict[str, str]) -> str:
    """A stand-in for "an old code path we kept for backward compatibility, that
    should nudge callers toward the replacement." Local to this file on purpose --
    nothing in src/shop currently needs a deprecation path.
    """
    warnings.warn(
        "_load_settings_v1 is deprecated, use Settings() directly", DeprecationWarning, stacklevel=2
    )
    return payload["database_url"]


def test_warns_checks_type_and_message() -> None:
    with pytest.warns(DeprecationWarning, match="use Settings"):
        _load_settings_v1({"database_url": "sqlite:///x"})
