"""What CI actually runs, proven locally with `pytester` (module 03's technique)
rather than requiring a real GitHub Actions run to see it work at all.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest


def test_junitxml_produces_a_parseable_report(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_passes():
            assert True

        def test_fails():
            assert 1 == 2
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--junitxml=report.xml")

    tree = ET.parse(pytester.path / "report.xml")
    root = tree.getroot()
    testsuite = root if root.tag == "testsuite" else root.find("testsuite")
    assert testsuite is not None
    assert testsuite.attrib["tests"] == "2"
    assert testsuite.attrib["failures"] == "1"


def test_coverage_fail_under_fails_the_build_when_coverage_is_low(
    pytester: pytest.Pytester,
) -> None:
    """A tiny throwaway project: one function, one test that only exercises HALF of
    it (an untested `if` branch) -- proving `coverage report --fail-under` actually
    fails the way `.github/workflows/ci.yml`'s "Enforce coverage floor" step relies
    on, not just trusting that it does.
    """
    pytester.makepyfile(
        mymodule="""
        def classify(n):
            if n > 0:
                return "positive"
            else:
                return "non-positive"
        """
    )
    pytester.makepyfile(
        test_mymodule="""
        from mymodule import classify

        def test_classify_positive():
            assert classify(1) == "positive"
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--cov=mymodule", "--cov-branch")
    result = pytester.run("coverage", "report", "--fail-under=95")

    assert result.ret != 0  # the gate correctly rejects the under-covered branch


def test_coverage_fail_under_passes_when_coverage_is_high_enough(
    pytester: pytest.Pytester,
) -> None:
    """Same module, this time with both branches covered -- the gate should pass."""
    pytester.makepyfile(
        mymodule="""
        def classify(n):
            if n > 0:
                return "positive"
            else:
                return "non-positive"
        """
    )
    pytester.makepyfile(
        test_mymodule="""
        from mymodule import classify

        def test_classify_positive():
            assert classify(1) == "positive"

        def test_classify_non_positive():
            assert classify(0) == "non-positive"
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--cov=mymodule", "--cov-branch")
    result = pytester.run("coverage", "report", "--fail-under=95")

    assert result.ret == 0
