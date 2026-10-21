"""Exercise: markers, skip/skipif, xfail, filterwarnings.

    make ex M=04

Two of these tasks (marking a test `unit`, adding a `skipif`) don't change whether
the test passes or fails on their own -- verify them by running, after you've made
the change (note the single `-m unit` here completely replaces this repo's default
`-m "not docker and not exercise"`, per the README, so exercise-marked tests are
still visible to it):
    uv run pytest modules/04-markers-and-config/exercises -m unit -v
and confirming `test_should_be_marked_unit` shows up.
"""

from __future__ import annotations

import sys
import warnings

import pytest

from shop.domain.errors import InvalidOrderError
from shop.domain.pricing import calculate_discount_cents


# TODO: add @pytest.mark.unit to this test (it's already registered in pyproject.toml).
@pytest.mark.unit
def test_should_be_marked_unit() -> None:
    assert calculate_discount_cents(0) == 0


@pytest.mark.skipif(sys.version_info < (3, 13), reason="uses a 3.13+ typing feature")
def test_skip_on_old_python() -> None:
    """TODO: add @pytest.mark.skipif above this function, skipping when
    sys.version_info is less than (3, 13), with a reason mentioning what feature
    needs it. You'll need to `import sys`.
    """
    assert True


@pytest.mark.xfail(reason="deliberately to be failed on purpose", strict=True)
def test_a_case_that_is_currently_genuinely_broken() -> None:
    """This assertion is wrong on purpose (a stand-in for a real, tracked bug).
    TODO: add @pytest.mark.xfail above this function with a reason, and strict=True
    (the default this repo recommends for a real, tracked failure).
    """
    assert calculate_discount_cents(10_000) == 999_999  # deliberately wrong


def _emits_a_warning() -> int:
    warnings.warn("this is expected in this one test", UserWarning, stacklevel=2)
    return 1


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_the_warning_is_expected_here() -> None:
    """TODO: add @pytest.mark.filterwarnings("ignore::UserWarning") above this
    function so the warning from _emits_a_warning() doesn't fail the test under this
    repo's ini-level `filterwarnings = ["error"]`.
    """
    assert _emits_a_warning() == 1


def test_negative_subtotal_still_raises() -> None:
    """No marker changes needed here -- included so `make ex M=04` has at least one
    case that should already pass once you've made the changes above and haven't
    broken anything else.
    """
    with pytest.raises(InvalidOrderError):
        calculate_discount_cents(-1)
