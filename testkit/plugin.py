"""The pytest plugin itself. Registered via the `pytest11` entry point in
pyproject.toml -- `uv sync` (which reinstalls this project editable) is what makes
pytest discover it automatically, in every test file in this repo, with zero
`conftest.py` imports needed. See modules/13-pytest-plugins/README.md.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from testkit.factories import ProductFactory
from testkit.fakes import FakeClock, FakeIdempotencyLock, FakePaymentGateway, FakeUnitOfWork


def pytest_addoption(parser: pytest.Parser) -> None:
    """A custom CLI option, available in every `uv run pytest ...` invocation once
    this plugin is installed -- try:
        uv run pytest modules/13-pytest-plugins/examples --fake-now=2030-06-15 -v
    and watch test_plugin_fixtures.py's clock-based test change what it asserts.
    """
    parser.addoption(
        "--fake-now",
        action="store",
        default="2026-01-01T00:00:00+00:00",
        help="ISO datetime the `fake_clock` fixture returns from .now() (testkit plugin).",
    )


@pytest.fixture
def fake_clock(request: pytest.FixtureRequest) -> FakeClock:
    fake_now = request.config.getoption("--fake-now")
    return FakeClock(datetime.fromisoformat(fake_now))


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def fake_lock() -> FakeIdempotencyLock:
    return FakeIdempotencyLock()


@pytest.fixture
def fake_gateway() -> FakePaymentGateway:
    return FakePaymentGateway()


@pytest.fixture
def product_factory() -> type[ProductFactory]:
    return ProductFactory
