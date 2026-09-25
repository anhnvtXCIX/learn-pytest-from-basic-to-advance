"""The fast, SQLite-backed integration tier: real SQLAlchemy, real SQL, no Docker.

Two things make this file worth reading closely, both found by actually running the
naive version of this pattern and watching it fail (not assumed from a blog post):

1. **pysqlite's BEGIN emulation breaks SAVEPOINT-based test isolation.** The
   standard SQLAlchemy recipe for per-test rollback wraps each test in an outer
   transaction and gives the session `join_transaction_mode="create_savepoint"`, so
   that even if application code calls `session.commit()` (ours does -- see
   `UnitOfWork`), it only releases a SAVEPOINT, and the outer transaction can still
   be rolled back at the end to undo everything. Empirically, against SQLite via
   aiosqlite, this ALONE does not work: rows committed by the "application code"
   survived the outer rollback. The cause is documented in SQLAlchemy's own SQLite
   dialect notes: pysqlite (the driver aiosqlite wraps) emits its own BEGIN
   statements based on heuristics that conflict with SQLAlchemy's SAVEPOINT usage.
   The fix is the `do_connect`/`do_begin` event listener pair below, which disables
   pysqlite's automatic BEGIN and lets SQLAlchemy issue it explicitly. Without both
   pieces together (join_transaction_mode AND these listeners), this fixture would
   silently leak state between tests -- exactly the "test interdependence" smell
   from docs/04-coverage-and-quality.md, and exactly the kind of bug that shows up
   as mysterious, order-dependent failures days later.

2. **Postgres (module 10) does not need the event-listener workaround** -- that's a
   pysqlite-specific quirk. `join_transaction_mode="create_savepoint"` alone is
   sufficient there, which is one more small, concrete reason SQLite and a real
   engine aren't interchangeable for integration testing (docs/05-backend-testing-playbook.md).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from shop.db import tables  # noqa: F401  -- registers the ORM tables on Base.metadata
from shop.db.base import Base


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Module-scoped deliberately: creating the engine and the schema once per file,
    not once per test, is the realistic shape (module 10's real Postgres container is
    session-scoped for the same reason -- it's expensive). Isolation between tests
    that share this one engine is `sessionmaker`'s job below, not this fixture's.

    Note the explicit `pytest_asyncio.fixture(..., loop_scope="module")` here,
    instead of the plain `@pytest.fixture` used everywhere else in this repo.
    pytest-asyncio ties an async fixture's event loop to a *loop scope* that
    defaults to "function"; a fixture wider than "function" (this one is "module")
    needs a matching, explicit `loop_scope` or it raises `ScopeMismatch` --
    confirmed by actually hitting that error while writing this fixture. See the
    module README for the full story, including why a `pytestmark =
    pytest.mark.asyncio(loop_scope="module")` on the TEST file alone is not enough
    on its own to fix a fixture's mismatch.
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
    """A sessionmaker bound to ONE connection and ONE outer transaction for the
    whole test. Every session it creates (including every session `UnitOfWork`
    creates internally, once per `uow_factory()` call) joins that same outer
    transaction as a SAVEPOINT. Rolling the outer transaction back at teardown
    undoes everything the test did, no matter how many times application code called
    `commit()` along the way.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        maker = async_sessionmaker(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield maker
        await trans.rollback()
