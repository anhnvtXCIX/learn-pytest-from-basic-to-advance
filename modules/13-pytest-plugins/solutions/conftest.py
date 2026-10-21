from __future__ import annotations

import contextlib

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    # exercises/conftest.py registers the same option once it's filled in, and a
    # whole-repo run (`make test`, CI) loads both conftests into one parser, where a
    # duplicate name raises ValueError. Whichever loads first wins; they're identical.
    with contextlib.suppress(ValueError):
        parser.addoption("--stock-qty", action="store", default="10")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    items.sort(key=lambda item: "zzz" in item.name)
