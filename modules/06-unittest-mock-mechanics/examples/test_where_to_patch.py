""""Where to patch" proven with two real, isolated pytest runs (pytester, from
module 03) instead of asserted in prose -- the whole point of this file is that this
mistake is easy to make and easy to demonstrate.

Scenario in both inner test files: `service.py` does `from greeter import
get_greeting` at import time, binding its OWN name `get_greeting` inside `service`'s
namespace. From then on, `service.greet()` looks up `get_greeting` in `service`'s
namespace -- it never looks back at `greeter` again.
"""

from __future__ import annotations

import pytest

_GREETER = """
def get_greeting():
    return "hello from the real implementation"
"""

_SERVICE = """
from greeter import get_greeting

def greet():
    return get_greeting()
"""


def test_patching_the_definition_site_has_no_effect(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(greeter=_GREETER, service=_SERVICE)
    pytester.makepyfile(
        test_wrong="""
        from unittest.mock import patch
        import service

        def test_patch_greeter_directly():
            with patch("greeter.get_greeting", return_value="mocked"):
                # service.greet() still uses the reference it imported BEFORE the
                # patch -- this assertion is checking that the WRONG patch target
                # had no effect, not asserting a mock worked.
                assert service.greet() == "hello from the real implementation"
        """
    )

    result = pytester.runpytest_subprocess("-p", "no:randomly")

    result.assert_outcomes(passed=1)


def test_patching_the_usage_site_works(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(greeter=_GREETER, service=_SERVICE)
    pytester.makepyfile(
        test_right="""
        from unittest.mock import patch
        import service

        def test_patch_service_import():
            with patch("service.get_greeting", return_value="mocked"):
                assert service.greet() == "mocked"
        """
    )

    result = pytester.runpytest_subprocess("-p", "no:randomly")

    result.assert_outcomes(passed=1)
