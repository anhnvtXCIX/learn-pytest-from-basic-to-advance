"""Per-test @pytest.mark.filterwarnings, narrowing the repo-wide `filterwarnings =
["error"]` for one specific, deliberate exception.
"""

from __future__ import annotations

import warnings

import pytest


def _deprecated_helper() -> int:
    warnings.warn("_deprecated_helper is going away", DeprecationWarning, stacklevel=2)
    return 42


def test_calling_the_deprecated_helper_would_normally_fail_the_test() -> None:
    """Without the marker below, this repo's ini-level `filterwarnings = ["error"]`
    would turn `_deprecated_helper`'s warning into an exception, failing the test --
    that's the whole point of the strict default. `pytest.raises` here proves it by
    demonstrating the warning genuinely becomes an error in the absence of an
    override.
    """
    with pytest.raises(DeprecationWarning):
        _deprecated_helper()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_the_one_place_we_still_call_the_deprecated_thing() -> None:
    """This marker narrows the override to DeprecationWarning specifically, and to
    this one test -- everywhere else in the suite, that same warning would still be
    promoted to an error.
    """
    assert _deprecated_helper() == 42
