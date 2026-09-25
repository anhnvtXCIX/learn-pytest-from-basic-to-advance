"""Exercise: implement pytest_addoption and pytest_collection_modifyitems yourself,
scoped to this directory (like examples/conftest.py, not like testkit/plugin.py).
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    # TODO: add a CLI option "--stock-qty" (action="store", default="10") that
    # test_plugin_exercise.py's stock-related test will read via
    # request.config.getoption("--stock-qty") to decide how much stock to seed.
    pass


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # TODO: sort `items` so that any test whose name contains "zzz" runs last,
    # regardless of pytest-randomly's shuffle order -- same technique as
    # examples/conftest.py, different substring.
    pass
