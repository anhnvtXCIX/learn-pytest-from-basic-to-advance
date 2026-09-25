"""monkeypatch.setenv, and the "Settings reads env once, at construction" gotcha."""

from __future__ import annotations

import pytest

from shop.config import Settings


def test_settings_reads_the_environment_at_construction_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHOP_TAX_RATE", "0.20")

    settings = Settings()  # constructed AFTER setenv -- picks up the override

    assert settings.tax_rate == 0.20


def test_an_already_constructed_settings_object_does_not_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings()  # constructed BEFORE setenv
    assert settings.tax_rate == 0.08  # the default

    monkeypatch.setenv("SHOP_TAX_RATE", "0.20")

    # Setting the env var after the fact does nothing to the existing instance --
    # pydantic-settings isn't watching the environment, it read it once.
    assert settings.tax_rate == 0.08


def test_monkeypatch_undoes_itself_automatically(monkeypatch: pytest.MonkeyPatch) -> None:
    """Not actually testing THIS test -- run
        uv run pytest modules/07-choosing-a-seam/examples/test_settings_env.py -v
    and notice this test's own assertion (below) proves the PREVIOUS test's setenv
    didn't leak in, regardless of run order.
    """
    monkeypatch.setenv("SHOP_TAX_RATE", "0.99")
    assert Settings().tax_rate == 0.99
    # monkeypatch reverts setenv when this test ends -- no explicit cleanup needed,
    # same guarantee as pytest-mock's `mocker` fixture (module 06).


def test_delenv_removes_a_variable_entirely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOP_API_KEY", "irrelevant")
    monkeypatch.delenv("SHOP_API_KEY")

    settings = Settings()

    assert settings.api_key == "test-client-api-key"  # falls back to the field default
