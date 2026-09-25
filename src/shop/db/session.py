"""Engine / session factory.

Deliberately just two small functions rather than a global engine. A module-level
global engine is convenient in a tutorial and a menace in a test suite: every test
that wants its own database (a fresh SQLite file, a Testcontainers Postgres) ends up
fighting the global. Fixtures build engines explicitly instead -- see
modules/09-integration-foundations/examples/conftest.py.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url, echo=echo)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
