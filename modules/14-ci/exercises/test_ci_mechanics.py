"""Exercise: JUnit XML and coverage gates, via pytester.

    make ex M=14
"""

from __future__ import annotations

import pytest


def test_junitxml_records_a_skipped_test(pytester: pytest.Pytester) -> None:
    """TODO: write an inner test file (pytester.makepyfile) with one test decorated
    @pytest.mark.skip(reason="...") and one plain passing test. Run it with
    --junitxml=report.xml (and -p no:randomly). Parse report.xml with
    xml.etree.ElementTree (see examples/test_ci_mechanics.py for the pattern) and
    assert the testsuite's "skipped" attribute is "1".
    """
    raise NotImplementedError("write this test")


def test_coverage_gate_at_100_percent_requires_every_branch(pytester: pytest.Pytester) -> None:
    """TODO: create a module with a function having an if/else, and a test file that
    covers only ONE branch. Run with --cov=<module> --cov-branch, then run
    `pytester.run("coverage", "report", "--fail-under=100")` and assert its `.ret`
    is nonzero (branch coverage below 100% correctly fails a --fail-under=100 gate).
    """
    raise NotImplementedError("write this test")
