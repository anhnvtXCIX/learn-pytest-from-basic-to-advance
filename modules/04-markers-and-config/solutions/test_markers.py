"""Reference solution for exercises/test_markers.py."""

from __future__ import annotations

import sys
import warnings

import pytest

from shop.domain.errors import InvalidOrderError
from shop.domain.pricing import calculate_discount_cents


@pytest.mark.unit
def test_should_be_marked_unit() -> None:
    assert calculate_discount_cents(0) == 0


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="not actually needed, but demonstrates skipif"
)
def test_skip_on_old_python() -> None:
    assert True


@pytest.mark.xfail(
    reason="known bug: discount tiers not yet applied above $100 -- see TICKET-999", strict=True
)
def test_a_case_that_is_currently_genuinely_broken() -> None:
    assert calculate_discount_cents(10_000) == 999_999  # deliberately wrong


def _emits_a_warning() -> int:
    warnings.warn("this is expected in this one test", UserWarning, stacklevel=2)
    return 1


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_the_warning_is_expected_here() -> None:
    assert _emits_a_warning() == 1


def test_negative_subtotal_still_raises() -> None:
    with pytest.raises(InvalidOrderError):
        calculate_discount_cents(-1)
