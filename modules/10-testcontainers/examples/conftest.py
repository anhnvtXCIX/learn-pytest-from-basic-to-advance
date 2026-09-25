"""The real-infra tier: an actual Postgres and an actual Redis, started in Docker by
Testcontainers, with the app's real Alembic migrations run against Postgres before
any test touches it.

Everything in this file is `docker`-marked (see the test files) and session-scoped:
starting a container takes real seconds, so this repo pays that cost once per test
session, not once per test. Isolation between tests that share this one Postgres is
the same `join_transaction_mode="create_savepoint"` technique from module 09 --
*without* module 09's pysqlite BEGIN workaround, because that workaround is specific
to pysqlite; verified by this file's own tests passing without it.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """Starts a real, throwaway Postgres in Docker for the whole test session.
    `driver="asyncpg"` makes `get_connection_url()` return a
    `postgresql+asyncpg://...` URL directly usable by our async engine.
    """
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
def redis_url() -> str:
    with RedisContainer("redis:8-alpine") as r:
        host = r.get_container_host_ip()
        port = r.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


def _run_migrations(database_url: str) -> None:
    """Runs the app's REAL Alembic migrations (migrations/versions/), not a
    `metadata.create_all()` shortcut (module 09 uses the shortcut deliberately; this
    tier's whole point is testing the real thing). Alembic's own `env.py` calls
    `asyncio.run(...)` internally -- which raises if called from inside an already-
    running event loop, hence running this function in a worker thread from the
    fixture below instead of awaiting it directly.
    """
    previous = os.environ.get("SHOP_DATABASE_URL")
    os.environ["SHOP_DATABASE_URL"] = database_url
    try:
        cfg = Config(str(REPO_ROOT / "alembic.ini"))
        command.upgrade(cfg, "head")
    finally:
        if previous is None:
            os.environ.pop("SHOP_DATABASE_URL", None)
        else:
            os.environ["SHOP_DATABASE_URL"] = previous


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine(postgres_url: str) -> AsyncIterator[AsyncEngine]:
    """`poolclass=NullPool` is load-bearing, not a style choice -- found the hard way.

    The first version of this fixture used SQLAlchemy's default pooled engine, the
    same as every other engine in this repo. Two tests, each just opening a
    connection and running a plain SELECT, back to back against this one
    session-scoped engine: the FIRST always passed, and the SECOND always failed --
    regardless of which test ran first, regardless of what either query was --
    with an opaque `asyncpg.exceptions.InterfaceError: cannot rollback; the
    transaction is in error state` raised from deep inside pool checkout, nowhere
    near any code in this repo. That symptom (works once, breaks on reuse) points at
    the pool handing back a connection whose asyncpg-level transaction state didn't
    get reset cleanly on checkin. `NullPool` sidesteps the question entirely by not
    pooling at all: every `engine.connect()` opens a brand-new physical connection
    and closes it for real afterward. Slower per-connection, and irrelevant here --
    this fixture already pays for a whole container per session; one more real TCP
    handshake per test is noise by comparison, and "always correct" beats "fast but
    only on the first use" for a test fixture.
    """
    await asyncio.to_thread(_run_migrations, postgres_url)
    eng = create_async_engine(postgres_url, poolclass=NullPool)
    yield eng
    await eng.dispose()


@pytest.fixture
async def sessionmaker(engine: AsyncEngine):
    """Same transaction-rollback-per-test pattern as module 09 -- no pysqlite
    workaround needed here, which is itself the point (see this module's README).
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        maker = async_sessionmaker(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield maker
        await trans.rollback()
