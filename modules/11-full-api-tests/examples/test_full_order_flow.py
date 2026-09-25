"""The happy path, end to end through real HTTP routing, a real (fast-tier)
database, and back -- plus the two scenarios that specifically need MULTIPLE
requests against the SAME app/database to mean anything: idempotent replay and a
genuine concurrent duplicate.
"""

from __future__ import annotations

import asyncio
import pathlib

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shop.api.app import create_app
from shop.api.deps import get_order_service
from shop.config import Settings
from shop.db.base import Base
from shop.db.uow import UnitOfWork
from shop.domain.models import Product
from shop.services.orders import OrderService

from .conftest import FakeClock, FakeIdempotencyLock, FakePaymentGateway


async def test_create_and_fetch_an_order(client, auth_headers, seeded_product: Product) -> None:
    create_response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 2}],
            "idempotency_key": "flow-key-1",
        },
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert body["status"] == "paid"
    assert body["total_cents"] == 3_000  # 2 * 1500, zero tax in this fixture setup

    get_response = await client.get(f"/orders/{body['id']}", headers=auth_headers)

    assert get_response.status_code == 200
    assert get_response.json() == body


async def test_idempotent_replay_returns_the_same_order_and_charges_once(
    client, auth_headers, seeded_product: Product, fake_gateway
) -> None:
    payload = {
        "customer_ref": "cust-1",
        "lines": [{"product_id": seeded_product.id, "quantity": 1}],
        "idempotency_key": "flow-key-replay",
    }

    first = await client.post("/orders", headers=auth_headers, json=payload)
    second = await client.post("/orders", headers=auth_headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(fake_gateway.charge_calls) == 1  # NOT charged twice


async def test_concurrent_duplicate_requests_only_one_wins(tmp_path: pathlib.Path) -> None:
    """Two requests, SAME idempotency key, fired at genuinely the same time (not one
    awaited after the other) -- this is what module 05's `FakeIdempotencyLock` and
    module 10's real Redis lock both exist to prevent from double-charging.

    This test deliberately does NOT use the module's shared `client`/`sessionmaker`
    fixtures. First version of this test did, and broke -- not sometimes, every
    time a random test-ordering happened to run something else afterward on the
    same connection. Cause: `sessionmaker` (conftest.py) binds every session to ONE
    shared connection specifically so a single test's writes can be rolled back
    cleanly (module 09's pattern). Two concurrent requests both opening/closing
    SAVEPOINTs on that SAME connection at the same time corrupts the savepoint
    stack (`OperationalError: no such savepoint`, or SQLAlchemy's own
    "nested transaction already deassociated from connection") -- the exact same
    "don't share one connection across concurrent work" lesson module 10's
    `test_concurrency.py` docstring explains, learned here the hard way a second
    time. The fix is the same: a real, independent, pooled engine, so each
    concurrent request gets its own connection. `tmp_path` (module 03) gives this
    test a real on-disk SQLite file -- `:memory:` databases are private to a single
    connection, and can't be shared across the pool concurrent connections need.
    """
    db_path = tmp_path / "concurrent.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            Product(id=0, sku="CONCURRENT-TEST", name="X", unit_price_cents=1_000, stock_qty=10)
        )
        await uow.commit()

    settings = Settings()
    application = create_app(settings)
    # `fake_lock` MUST be built once, outside the lambda below. FastAPI calls a
    # `dependency_overrides` callable fresh for EVERY request -- building the fake
    # lock (or gateway) *inside* the lambda gives each of the two concurrent
    # requests its own, unshared lock, defeating the entire point (found by hitting
    # a duplicate-key IntegrityError here instead of the expected 409: both
    # requests' `acquire()` calls "succeeded" because they were never actually
    # contending for the same lock object).
    fake_lock = FakeIdempotencyLock()
    fake_gateway = FakePaymentGateway()
    application.dependency_overrides[get_order_service] = lambda: OrderService(
        uow_factory=lambda: UnitOfWork(sessionmaker),
        payment_gateway=fake_gateway,
        idempotency_lock=fake_lock,
        clock=FakeClock(),
        tax_rate=0.0,
    )

    payload = {
        "customer_ref": "cust-1",
        "lines": [{"product_id": product.id, "quantity": 1}],
        "idempotency_key": "flow-key-concurrent",
    }

    try:
        async with application.router.lifespan_context(application):
            transport = ASGITransport(app=application)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                headers = {"X-API-Key": settings.api_key}
                responses = await asyncio.gather(
                    client.post("/orders", headers=headers, json=payload),
                    client.post("/orders", headers=headers, json=payload),
                )
    finally:
        await engine.dispose()

    statuses = sorted(r.status_code for r in responses)
    assert statuses == [201, 409]  # one created, one told "already in flight"


async def test_cancel_a_paid_order_refunds_and_restocks(
    client, auth_headers, seeded_product: Product, fake_gateway
) -> None:
    create_response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "flow-key-cancel",
        },
    )
    order_id = create_response.json()["id"]

    cancel_response = await client.post(f"/orders/{order_id}/cancel", headers=auth_headers)

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "refunded"
    assert len(fake_gateway.refund_calls) == 1
