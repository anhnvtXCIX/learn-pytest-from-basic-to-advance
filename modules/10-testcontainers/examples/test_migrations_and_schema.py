"""Proves the REAL Alembic migrations (not module 09's metadata.create_all shortcut)
actually apply cleanly against Postgres, and exercises the two dialect-sensitive
columns from src/shop/db/tables.py.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.docker


async def test_migrations_created_every_expected_table(engine: AsyncEngine) -> None:
    # A plain query against information_schema rather than SQLAlchemy's `Inspector`
    # -- simpler, and consistent with the rest of this file. (The real fix for a
    # much stranger bug hit while building this fixture -- whichever test ran
    # SECOND against the shared engine failed with an opaque asyncpg "transaction is
    # in error state" error, no matter what either test's query was -- turned out to
    # be `poolclass=NullPool` in conftest.py's `engine` fixture, not anything about
    # this specific query. See that fixture's comment for the full story.)
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        table_names = {row[0] for row in result}

    assert {"products", "orders", "order_lines", "alembic_version"} <= table_names


async def test_metadata_column_is_real_jsonb_on_postgres(engine: AsyncEngine) -> None:
    """OrderRow.metadata_ uses JSON().with_variant(JSONB, "postgresql") -- confirming
    it's ACTUALLY jsonb here (not just "some JSON-shaped text column") matters
    because JSONB supports indexing and containment queries (`@>`) that a text
    column doesn't; module 09 has no way to check this at all since SQLite doesn't
    have a JSONB type to be wrong about.
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'orders' AND column_name = 'metadata'"
            )
        )
        (data_type,) = result.one()

    assert data_type == "jsonb"
