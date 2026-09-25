# 10. Real infra with Testcontainers

This module runs the app's real Alembic migrations against a real, throwaway
Postgres (and a real Redis), both started in Docker by
[Testcontainers](https://testcontainers-python.readthedocs.io/), and proves three
things module 09's SQLite tier cannot: real row-level locking, real dialect-specific
exception types, and real JSONB. Getting there surfaced three genuine bugs, not
assumed from a tutorial -- read on, because each one is a real lesson.

## Setup

Needs a running Docker daemon. Nothing else — `Testcontainers` pulls
`postgres:17-alpine` and `redis:8-alpine` the first time you run this module (cached
after that) and tears both containers down automatically at the end of the test
session.

```bash
make test-docker           # everything in this module (and any other `docker`-marked test)
uv run pytest modules/10-testcontainers/examples -m docker -v   # just this module, verbose
```

If Docker isn't running, `make test` (the default) never touches this module at all
— `docker`-marked tests are deselected by `addopts`, same mechanism as `exercise`.

## Bug #1: `NullPool` is load-bearing, not a style choice

The `engine` fixture (`examples/conftest.py`) uses `poolclass=NullPool` — every
other engine in this repo uses SQLAlchemy's default pooled engine. This isn't
stylistic. The first version of this fixture used the default pool, and two tests
sharing one session-scoped engine — each just opening a connection and running a
plain `SELECT` — showed a bizarre pattern: **the first always passed, the second
always failed**, regardless of which test ran first or what either query was, with

```
asyncpg.exceptions.InterfaceError: cannot rollback; the transaction is in error state
```

raised from deep inside connection-pool checkout, nowhere near any code in this
repo. That symptom — works once, breaks on reuse — points at the pool handing back a
connection whose asyncpg-level transaction state wasn't reset cleanly on checkin.
`NullPool` sidesteps the question by not pooling at all: every `engine.connect()`
opens a real, fresh physical connection. Slower per-connection, irrelevant here — one
more real TCP handshake is noise next to the cost of starting the container itself,
and "always correct" beats "fast but broken on the second use" for a test fixture.

## Bug #2: Postgres aborts the whole transaction on a failed statement

`examples/test_dialect_divergence.py` needs `pytest.raises(IntegrityError)` to wrap
the **entire** `async with UnitOfWork(...) as uow:` block, not just the inner
`.add()` call that actually raises — the opposite of what feels natural, and the
opposite of what module 09's SQLite version of the same test does. The reason:
once a statement inside a Postgres transaction fails, Postgres aborts the *whole*
transaction ("current transaction is aborted, commands ignored until end of
transaction block") until something rolls it back. `UnitOfWork.__aexit__` only calls
`session.rollback()` when it *sees* an exception propagate out of the `async with`
block; catching the error *inside* the block hides it from `__aexit__`, leaves the
aborted transaction un-rolled-back, and breaks the next thing that touches that
session. SQLite has no equivalent "poisoned transaction" state — which is exactly
why module 09's version of this test gets away with a pattern that breaks here.
**The takeaway isn't "remember this one quirk"** — it's that a test pattern verified
against SQLite is not automatically safe to reuse verbatim against Postgres, which is
the whole reason this tier exists.

## Bug #3: `join_transaction_mode="create_savepoint"` needs no pysqlite-style workaround here

Module 09 needed a pair of SQLAlchemy event listeners to make per-test rollback work
against SQLite (a pysqlite driver quirk). `examples/conftest.py`'s `sessionmaker`
fixture is the *exact same pattern*, minus those listeners — and it works, confirmed
by `examples/test_dialect_divergence.py` and `test_redis_lock.py`'s independent
tests all passing cleanly in any order. One more concrete data point for "SQLite and
Postgres are not interchangeable for integration testing."

## The actual payoff: a real race condition, really prevented

`examples/test_concurrency.py` is why this whole tier exists. It launches two
**genuinely independent** database connections (deliberately not through the
rollback-per-test `sessionmaker` — see the file's docstring for why that would
defeat the point) both trying to reserve the last unit of a product's stock, via
`asyncio.gather`. `ProductRepository.reserve_stock`'s `.with_for_update()` (silently
a no-op on SQLite, module 09) makes Postgres serialize them: exactly one succeeds,
the other correctly sees zero stock left and raises `InsufficientStockError`. This is
not something any fake (module 05) or any amount of mocking (modules 06-08) could
ever have proven — it requires two real connections and a real database enforcing a
real lock.

## Real JSONB, real dialect-specific exceptions

`examples/test_migrations_and_schema.py` confirms `OrderRow.metadata_` is *actually*
`jsonb` in Postgres's `information_schema` (SQLite has no JSONB type to be wrong
about). `examples/test_dialect_divergence.py` confirms the same UNIQUE-constraint
violation raises SQLAlchemy's `IntegrityError` on both engines, but the driver
exception wrapped inside it (`.orig`) is a *specific* `UniqueViolationError` on
Postgres vs. a single generic `sqlite3.IntegrityError` covering every constraint
kind on SQLite — code that wants to tell "which constraint failed" apart from "some
constraint failed" can do it precisely on one engine and not the other.

## Exercise

```bash
make ex M=10
```

(Requires Docker; run `make test-docker` afterward, not `make ex M=10` on its own,
since `-m exercise` on the command line replaces the default marker filter entirely
— see module 04 — and would try to run every `exercise`-marked test including
`docker`-marked ones without also opting into Docker.)

## You should now be able to

- Explain, from this module's real debugging history, why `NullPool` matters for
  async test engines and recognize the "works once, breaks on reuse" symptom.
- Explain why a `pytest.raises` block needs to wrap a whole `UnitOfWork` context on
  Postgres in a way it doesn't need to on SQLite.
- Write (or read and explain) a genuine concurrency test using two independent
  connections and `asyncio.gather`.
- State at least three concrete things this tier catches that module 09 cannot.

## References

- Testcontainers for Python docs — https://testcontainers-python.readthedocs.io/
- SQLAlchemy docs, connection pooling (`NullPool`) —
  https://docs.sqlalchemy.org/en/20/core/pooling.html
- PostgreSQL docs, "Errors and Rollbacks" (the aborted-transaction behavior) —
  https://www.postgresql.org/docs/current/tutorial-transactions.html
