"""Proves conftest.py layering: this directory's `tax_rate` fixture (0.20) wins over
../conftest.py's (0.08) for every test in here.
"""

from __future__ import annotations

from shop.domain.pricing import calculate_tax_cents


def test_nested_conftest_fixture_wins(tax_rate: float) -> None:
    assert tax_rate == 0.20  # the override, not the outer 0.08


def test_using_the_overridden_rate_in_a_calculation(tax_rate: float) -> None:
    assert calculate_tax_cents(1_000, tax_rate) == 200
