"""A Redis-backed distributed lock, used to stop two concurrent requests carrying the
same idempotency key from both proceeding to charge the payment gateway.

A row-level DB lock (see db/repository.py's `reserve_stock`) isn't enough for this by
itself: by the time two concurrent requests both reach the database, one has usually
already committed a partial order. The lock needs to be acquired *before* either
request starts doing work, which is exactly what Redis's atomic `SET ... NX` gives us.

This is also the module's Redis seam: `IdempotencyLock` is a `Protocol`, so unit tests
(module 05) can use a trivial in-memory fake, while modules 10-11 exercise the real
thing against Testcontainers' Redis -- where TTL expiry and cross-connection visibility
are actually real.
"""

from __future__ import annotations

from typing import Protocol

import redis.asyncio as redis


class IdempotencyLock(Protocol):
    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        """Return True if the lock was acquired, False if someone else holds it."""
        ...

    async def release(self, key: str) -> None: ...


class RedisIdempotencyLock:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        acquired = await self._client.set(f"order-lock:{key}", "1", nx=True, ex=ttl_seconds)
        return bool(acquired)

    async def release(self, key: str) -> None:
        await self._client.delete(f"order-lock:{key}")
