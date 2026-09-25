"""xfail, and specifically what `strict` changes -- proven with `pytester` rather
than asserted in prose, since a real strict-xfail-that-passes would break our own
`make test` if we kept it lying around (module 03 introduces this technique).
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="genuinely broken right now, tracked as a real xfail")
def test_a_genuinely_failing_case_reports_as_xfail() -> None:
    assert 1 == 2  # actually fails -> XFAIL, not a suite failure


def test_strict_false_lets_an_unexpected_pass_through_quietly(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.xfail(reason="thought this was broken", strict=False)
        def test_actually_passes():
            assert 1 == 1
        """
    )

    result = pytester.runpytest_subprocess("-p", "no:randomly", "-rxX")

    result.assert_outcomes(xpassed=1)  # reported, but the run is still green


def test_strict_true_turns_an_unexpected_pass_into_a_failure(pytester: pytest.Pytester) -> None:
    """Same scenario as above, `strict=True` -- the ONLY difference -- and the run
    goes red instead of green. This is why `strict=True` should be your default.
    """
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.xfail(reason="thought this was broken", strict=True)
        def test_actually_passes():
            assert 1 == 1
        """
    )

    result = pytester.runpytest_subprocess("-p", "no:randomly", "-rxX")

    result.assert_outcomes(failed=1)
