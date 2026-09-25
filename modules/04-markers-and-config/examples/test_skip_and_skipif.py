"""skip and skipif: for tests that CANNOT meaningfully run right now, not for tests
that are failing for a real reason.
"""

from __future__ import annotations

import sys

import pytest


@pytest.mark.skip(reason="placeholder: demonstrates unconditional skip -- see -rs output")
def test_unconditionally_skipped() -> None:
    raise AssertionError("never runs")


@pytest.mark.skipif(sys.version_info < (3, 13), reason="uses a 3.13+ typing feature")
def test_skipped_on_old_python() -> None:
    from datetime import UTC  # noqa: F401  -- available from Python 3.11+, used here as a stand-in

    assert True


@pytest.mark.skipif(
    sys.platform == "win32", reason="path separators differ; not worth handling here"
)
def test_skipped_on_windows_only() -> None:
    import pathlib

    assert str(pathlib.PurePosixPath("a/b")) == "a/b"
