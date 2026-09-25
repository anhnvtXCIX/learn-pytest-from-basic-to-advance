"""Full-stack API test harness: the REAL FastAPI app, a REAL (fast, SQLite-tier)
database via module 09's transaction-rollback-per-test pattern, and a FAKE payment
gateway/lock/clock (module 05) swapped in via `app.dependency_overrides` (module 07).

This is the concrete answer to "how real should a test be": real enough to catch
routing, validation, and database-integration bugs; fake at the one boundary
(a third-party payment processor) where "real" would mean a network call in every
test run.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from polyfactory.factories import DataclassFactory
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from shop.api.app import create_app
from shop.api.deps import get_order_service
from shop.config import Settings
from shop.db import tables  # noqa: F401
from shop.db.base import Base
from shop.db.uow import UnitOfWork
from shop.domain.errors import PaymentDeclinedError
from shop.domain.models import Product
from shop.services.orders import OrderService


class ProductFactory(DataclassFactory[Product]):
    __model__ = Product


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=UTC)


class FakePaymentGateway:
    """Declines anything over $1,000 -- enough behavior to exercise the 402 path
    (see test_error_paths.py) without needing respx/real HTTP (module 08's job).
    """

    def __init__(self) -> None:
        self.charge_calls: list[dict] = []
        self.refund_calls: list[dict] = []

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        self.charge_calls.append(
            {"amount_cents": amount_cents, "currency": currency, "reference": reference}
        )
        if amount_cents > 100_000:
            raise PaymentDeclinedError(reason="amount exceeds limit")
        return f"pay_{reference}"

    async def refund(self, *, payment_reference: str, amount_cents: int) -> None:
        self.refund_calls.append(
            {"payment_reference": payment_reference, "amount_cents": amount_cents}
        )


class FakeIdempotencyLock:
    def __init__(self) -> None:
        self._held: set[str] = set()

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        if key in self._held:
            return False
        self._held.add(key)
        return True

    async def release(self, key: str) -> None:
        self._held.discard(key)


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Same fast SQLite tier as module 09 -- see that module's README for why the
    event listeners below are required, not optional, for rollback-per-test to work.
    """
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(eng.sync_engine, "connect")
    def _disable_pysqlite_begin_emulation(dbapi_connection, connection_record) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(eng.sync_engine, "begin")
    def _emit_our_own_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN")

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    await eng.dispose()


@pytest.fixture
async def sessionmaker(engine: AsyncEngine):
    async with engine.connect() as conn:
        trans = await conn.begin()
        maker = async_sessionmaker(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield maker
        await trans.rollback()


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def fake_gateway() -> FakePaymentGateway:
    return FakePaymentGateway()


@pytest.fixture
def fake_lock() -> FakeIdempotencyLock:
    return FakeIdempotencyLock()


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    return {"X-API-Key": settings.api_key}


@pytest.fixture
async def app(sessionmaker, settings: Settings, fake_gateway: FakePaymentGateway, fake_lock):
    application = create_app(settings)
    application.dependency_overrides[get_order_service] = lambda: OrderService(
        uow_factory=lambda: UnitOfWork(sessionmaker),
        payment_gateway=fake_gateway,
        idempotency_lock=fake_lock,
        clock=FakeClock(),
        tax_rate=0.0,
    )
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def seeded_product(sessionmaker) -> Product:
    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            ProductFactory.build(unit_price_cents=1_500, stock_qty=5)
        )
        await uow.commit()
    return product
