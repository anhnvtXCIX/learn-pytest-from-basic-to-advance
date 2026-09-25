"""Mock/MagicMock/AsyncMock, call assertions, and side_effect."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from shop.domain.errors import PaymentGatewayUnavailableError


def test_bare_mock_accepts_anything_including_typos() -> None:
    """The dangerous convenience: nothing here would catch a typo'd method name."""
    mock_gateway = Mock()

    mock_gateway.charge(amount_cents=100)  # fine
    mock_gateway.chrage(amount_cents=100)  # ALSO "fine" -- typo, silently accepted

    assert mock_gateway.charge.called
    assert mock_gateway.chrage.called  # proves the typo was never caught


def test_call_assertions() -> None:
    mock_fn = Mock(return_value="ok")

    result = mock_fn(1, key="value")

    assert result == "ok"
    mock_fn.assert_called_once_with(1, key="value")
    assert mock_fn.call_count == 1
    assert mock_fn.call_args.args == (1,)
    assert mock_fn.call_args.kwargs == {"key": "value"}


def test_magicmock_supports_dunder_methods() -> None:
    plain = Mock()
    magic = MagicMock()

    with pytest.raises(TypeError):
        len(plain)  # plain Mock doesn't implement __len__

    magic.__len__.return_value = 3
    assert len(magic) == 3  # MagicMock does


async def test_asyncmock_must_be_used_for_async_methods() -> None:
    """This is the mistake this repo's README warns about: use a plain Mock for an
    `async def` method, and awaiting its call result raises TypeError.
    """
    wrong = Mock(return_value="result")
    with pytest.raises(TypeError, match="can't be used in 'await' expression"):
        await wrong()  # Mock() returns a plain string, not a coroutine

    right = AsyncMock(return_value="result")
    assert await right() == "result"  # AsyncMock() returns an awaitable


async def test_asyncmock_await_assertions() -> None:
    mock_charge = AsyncMock(return_value="pay_ref")

    result = await mock_charge(amount_cents=1_000, currency="usd", reference="key-1")

    assert result == "pay_ref"
    mock_charge.assert_awaited_once_with(amount_cents=1_000, currency="usd", reference="key-1")
    assert mock_charge.await_count == 1


async def test_side_effect_can_raise() -> None:
    mock_charge = AsyncMock(side_effect=PaymentGatewayUnavailableError("timed out"))

    with pytest.raises(PaymentGatewayUnavailableError, match="timed out"):
        await mock_charge(amount_cents=100, currency="usd", reference="key-1")


async def test_side_effect_can_vary_per_call() -> None:
    """First call fails, second succeeds -- useful for testing code that retries.
    (OrderService itself doesn't retry -- see module 08's README for why -- but the
    mechanic is worth knowing regardless.)
    """
    mock_charge = AsyncMock(
        side_effect=[PaymentGatewayUnavailableError("timed out"), "pay_ref_ok"]
    )

    with pytest.raises(PaymentGatewayUnavailableError):
        await mock_charge(amount_cents=100, currency="usd", reference="key-1")

    result = await mock_charge(amount_cents=100, currency="usd", reference="key-1")
    assert result == "pay_ref_ok"


async def test_side_effect_as_a_callable_computes_from_the_real_arguments() -> None:
    async def _side_effect(*, amount_cents: int, currency: str, reference: str) -> str:
        if amount_cents > 100_000:
            raise PaymentGatewayUnavailableError("too large for this fake path")
        return f"pay_{reference}"

    mock_charge = AsyncMock(side_effect=_side_effect)

    assert await mock_charge(amount_cents=500, currency="usd", reference="abc") == "pay_abc"
    with pytest.raises(PaymentGatewayUnavailableError):
        await mock_charge(amount_cents=200_000, currency="usd", reference="abc")
