"""The app factory.

Everything is built here and hung off `app.state` rather than as module-level
globals, specifically so that `create_app(settings=...)` can be called more than once
in a single test process (e.g. one Postgres-backed app per Testcontainers-scoped test
session) without any shared, leaking state between them.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as redis
from fastapi import FastAPI

from shop.api.routes import router
from shop.clock import SystemClock
from shop.config import Settings, get_settings
from shop.db.session import build_engine, build_sessionmaker
from shop.db.uow import UnitOfWork
from shop.gateways.cache import RedisIdempotencyLock
from shop.gateways.payments import HttpPaymentGateway
from shop.services.orders import OrderService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings.database_url)
        sessionmaker = build_sessionmaker(engine)
        http_client = httpx.AsyncClient(base_url=settings.payment_gateway_url, timeout=5.0)
        redis_client = redis.from_url(settings.redis_url)

        app.state.settings = settings
        app.state.engine = engine
        app.state.order_service = OrderService(
            uow_factory=lambda: UnitOfWork(sessionmaker),
            payment_gateway=HttpPaymentGateway(
                http_client, api_key=settings.payment_gateway_api_key
            ),
            idempotency_lock=RedisIdempotencyLock(redis_client),
            clock=SystemClock(),
            tax_rate=settings.tax_rate,
        )
        try:
            yield
        finally:
            await http_client.aclose()
            await redis_client.aclose()
            await engine.dispose()

    app = FastAPI(title="Shop Orders API", lifespan=lifespan)
    app.include_router(router)
    return app
