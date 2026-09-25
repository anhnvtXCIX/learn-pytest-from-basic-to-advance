"""Proves the per-test rollback pattern actually isolates tests that share ONE
engine: both tests below insert a product with the SAME unique sku. If rollback
didn't clean up after whichever test ran first (pytest-randomly decides), the
second one would fail with a UNIQUE constraint violation.
"""

from __future__ import annotations

from shop.db.repository import ProductRepository
from shop.domain.models import Product

# Nothing test-loop-scope-related needed here, even though `engine` (conftest.py) is
# module-scoped: the fixture declares its OWN `loop_scope="module"` via
# `pytest_asyncio.fixture(...)`, which turned out to be sufficient on its own --
# tried adding a `pytestmark = pytest.mark.asyncio(loop_scope="module")` here too
# while writing this file, on the assumption both sides needed to agree, and
# confirmed by testing without it that it changed nothing. See conftest.py's
# `engine` fixture for where the actual fix lives, and the module README for the
# `ScopeMismatch` error this setup avoids.


async def test_insert_widget_a(sessionmaker) -> None:
    async with sessionmaker() as session:
        repo = ProductRepository(session)
        await repo.add(Product(id=0, sku="SHARED-SKU", name="A", unit_price_cents=100, stock_qty=1))
        await session.commit()


async def test_insert_widget_b(sessionmaker) -> None:
    """If test_insert_widget_a's row leaked, this commit would raise IntegrityError
    (UNIQUE constraint failed: products.sku) -- it doesn't, proving rollback worked.
    """
    async with sessionmaker() as session:
        repo = ProductRepository(session)
        await repo.add(Product(id=0, sku="SHARED-SKU", name="B", unit_price_cents=200, stock_qty=1))
        await session.commit()
