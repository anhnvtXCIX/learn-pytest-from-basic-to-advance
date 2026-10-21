"""Exercise: JUnit XML and coverage gates, via pytester.

make ex M=14
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest


def test_junitxml_records_a_skipped_test(pytester: pytest.Pytester) -> None:
    """TODO: write an inner test file (pytester.makepyfile) with one test decorated
    @pytest.mark.skip(reason="...") and one plain passing test. Run it with
    --junitxml=report.xml (and -p no:randomly). Parse report.xml with
    xml.etree.ElementTree (see examples/test_ci_mechanics.py for the pattern) and
    assert the testsuite's "skipped" attribute is "1".
    """
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.skip(reason="I want to skip it")
        def test_skip():
            # Don't want to test. That's it
            pass
            
        def test_obvious_passing():
            assert 1 < 2
        """
    )
    pytester.runpytest_subprocess("-p", "no:randomly", "--junitxml=report.xml")

    tree = ET.parse(pytester.path / "report.xml")
    root = tree.getroot()
    testsuite = root if root.tag == "testsuite" else root.find("testsuite")
    assert testsuite is not None
    assert testsuite.attrib["tests"] == "2"
    assert testsuite.attrib["skipped"] == "1"


def test_coverage_gate_at_100_percent_requires_every_branch(pytester: pytest.Pytester) -> None:
    """TODO: create a module with a function having an if/else, and a test file that
    covers only ONE branch. Run with --cov=<module> --cov-branch, then run
    `pytester.run("coverage", "report", "--fail-under=100")` and assert its `.ret`
    is nonzero (branch coverage below 100% correctly fails a --fail-under=100 gate).
    """
    pytester.makepyfile(
        mymodule="""
            def is_greater_than_0(n: int) -> bool:
                if n > 0:
                    return True
                else:
                    return False

            def test_greater_than_0():
                assert is_greater_than_0(100) is True
        """
    )

    pytester.runpytest_subprocess("-p", "no:randomly", "--cov=mymodule", "--cov-branch")
    result = pytester.run("coverage", "report", "--fail-under=100")

    assert result.ret != 0
