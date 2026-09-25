"""Unit of Work: one transaction, two repositories.

Bundling `ProductRepository` and `OrderRepository` behind a single object that owns
the session means `OrderService` (services/orders.py) can reserve stock and record an
order in the *same* database transaction -- if the payment gateway call after that
fails, `__aexit__` rolls everything back. Without this, a partial failure could leave
stock reserved for an order that was never actually created.

Reference: Percival & Gregory, ch. 6 -- https://www.cosmicpython.com/book/chapter_06_uow.html
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shop.db.repository import (
    OrderRepository,
    ProductRepository,
    SupportsOrderRepository,
    SupportsProductRepository,
)


class UnitOfWork:
    """Concrete, SQLAlchemy-backed Unit of Work.

    `OrderService` (services/orders.py) is typed against `SupportsUnitOfWork` below,
    not against this class -- so module 05's `FakeUnitOfWork` (plain dicts, no
    database at all) is a drop-in substitute for unit tests.
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker
        self._session: AsyncSession | None = None
        self._products: ProductRepository | None = None
        self._orders: OrderRepository | None = None

    @property
    def products(self) -> ProductRepository:
        assert self._products is not None, "use 'async with UnitOfWork(...) as uow' first"
        return self._products

    @property
    def orders(self) -> OrderRepository:
        assert self._orders is not None, "use 'async with UnitOfWork(...) as uow' first"
        return self._orders

    async def __aenter__(self) -> UnitOfWork:
        self._session = self._sessionmaker()
        self._products = ProductRepository(self._session)
        self._orders = OrderRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()


class SupportsUnitOfWork(Protocol):
    """What `OrderService` actually depends on: an async context manager exposing a
    product repository, an order repository, and a commit(). Both `UnitOfWork` above
    and `testkit`'s `FakeUnitOfWork` satisfy this without either knowing about the
    other -- structural typing is what makes the fake a legitimate substitute rather
    than a hack.
    """

    @property
    def products(self) -> SupportsProductRepository: ...

    @property
    def orders(self) -> SupportsOrderRepository: ...

    async def __aenter__(self) -> SupportsUnitOfWork: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
