"""The unmodified `tax_rate` fixture from conftest.py, for contrast with
nested/test_override.py's overridden value.
"""

from __future__ import annotations


def test_outer_tax_rate_is_the_conftest_default(tax_rate: float) -> None:
    assert tax_rate == 0.08
