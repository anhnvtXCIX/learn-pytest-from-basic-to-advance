"""Reference solution for exercises/test_ci_mechanics.py."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest


def test_junitxml_records_a_skipped_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.skip(reason="not ready yet")
        def test_not_ready():
            assert False

        def test_ready():
            assert True
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--junitxml=report.xml")

    tree = ET.parse(pytester.path / "report.xml")
    root = tree.getroot()
    testsuite = root if root.tag == "testsuite" else root.find("testsuite")
    assert testsuite is not None
    assert testsuite.attrib["skipped"] == "1"


def test_coverage_gate_at_100_percent_requires_every_branch(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        mymodule="""
        def sign(n):
            if n >= 0:
                return "non-negative"
            else:
                return "negative"
        """
    )
    pytester.makepyfile(
        test_mymodule="""
        from mymodule import sign

        def test_sign_non_negative():
            assert sign(1) == "non-negative"
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--cov=mymodule", "--cov-branch")
    result = pytester.run("coverage", "report", "--fail-under=100")

    assert result.ret != 0
