"""Exercise: the `engine` fixture below is BROKEN on purpose -- it's missing the fix
from examples/conftest.py. Running `make ex M=09` right now fails with:

    ScopeMismatch: You tried to access the function scoped fixture
    _function_scoped_runner with a module scoped request object.

TODO: fix `engine` below the same way examples/conftest.py does:
  1. Import `pytest_asyncio`.
  2. Change `@pytest.fixture(scope="module")` to
     `@pytest_asyncio.fixture(scope="module", loop_scope="module")`.

(`sessionmaker` below is already correct and doesn't need changes -- it's
function-scoped, which matches the default loop scope.)
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from shop.db import tables  # noqa: F401
from shop.db.base import Base


@pytest.fixture(scope="module")  # TODO: needs to be pytest_asyncio.fixture with loop_scope="module"
async def engine() -> AsyncIterator[AsyncEngine]:
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
