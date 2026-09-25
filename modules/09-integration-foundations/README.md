# 09. Integration foundations

Read `docs/05-backend-testing-playbook.md`'s database section first. This module
builds the fast, SQLite-backed integration tier concretely -- and documents two real
bugs found while building it, not assumed from a tutorial.

## What "integration" means for this tier

Real SQLAlchemy, a real (in-memory) SQLite engine, real SQL executed -- but a fake
payment gateway and idempotency lock (module 05's fakes), because "real" for a
database we own and "real" for a third party we don't are different decisions
(`docs/05`). This tier's job is to catch bugs in *our* query logic and *our*
transaction handling; module 10 adds the tier that catches bugs SQLite can't.

## The transaction-rollback-per-test pattern, and what it took to make it actually work

The standard approach: wrap each test in one outer database transaction, give the
`Session` a `join_transaction_mode="create_savepoint"` so that even if application
code calls `commit()` (`UnitOfWork` does), it only releases a SAVEPOINT, then roll
the *outer* transaction back at teardown to undo everything.

That's the textbook version. Building it for this repo, **the textbook version
alone did not work against SQLite**: rows committed by application code survived the
outer rollback. The cause, tracked down and fixed in `examples/conftest.py`: the
`pysqlite` driver (which `aiosqlite` wraps) emits its own `BEGIN` statements based on
heuristics that fight with SQLAlchemy's SAVEPOINT-based nesting. The fix is a pair of
SQLAlchemy event listeners that disable pysqlite's automatic transaction handling and
let SQLAlchemy issue `BEGIN` itself — see the `engine` fixture's docstring for the
exact code and the empirical proof (this doc isn't asking you to trust it: run
`examples/test_rollback_isolation.py`, which would fail with a UNIQUE constraint
violation if the fix weren't there, since both its tests insert the same SKU and
depend entirely on rollback cleaning up between them).

**Postgres does not need this workaround** — it's a pysqlite-specific quirk.
`join_transaction_mode="create_savepoint"` alone is sufficient there (module 10).
One more concrete reason SQLite and Postgres aren't interchangeable for integration
testing.

## The pytest-asyncio loop-scope trap

`examples/conftest.py`'s `engine` fixture is `scope="module"` (creating a real
engine once per file, not once per test — the realistic shape; module 10's
Testcontainers Postgres is `session`-scoped for the same reason). The very first
version of this fixture used plain `@pytest.fixture`, and hitting `uv run pytest`
produced:

```
ScopeMismatch: You tried to access the function scoped fixture _function_scoped_runner
with a module scoped request object.
```

pytest-asyncio ties an async fixture's event loop to a **loop scope**, which
defaults to `"function"` (this repo's `asyncio_default_fixture_loop_scope =
"function"` in `pyproject.toml`, following the current pytest-asyncio default). A
`module`-scoped async fixture needs a loop that lives at least that long, or you get
exactly this error. The fix is `pytest_asyncio.fixture(scope="module",
loop_scope="module")` — an explicit import of `pytest_asyncio` and its own
`fixture` decorator, instead of the plain `@pytest.fixture` used everywhere else in
this repo, specifically because *this one fixture* needs a wider loop than the
default.

One thing that turned out **not** to be necessary, despite seeming like it should be:
adding `pytestmark = pytest.mark.asyncio(loop_scope="module")` to the *test* files
using this fixture. Tested directly (see the comments in
`examples/test_rollback_isolation.py`) — the fixture's own `loop_scope` was
sufficient by itself. Worth knowing, because plenty of blog posts (and outdated
advice from before pytest-asyncio 1.0 removed the old `event_loop` fixture entirely)
will tell you both sides need to agree.

## `metadata.create_all()` vs. real Alembic migrations

This tier uses `Base.metadata.create_all()` as a fast shortcut for schema setup, not
the real Alembic migrations the app actually ships with. That's a deliberate scope
line, not an oversight: testing that your *migrations themselves* are correct (do
they apply cleanly, do they round-trip) is a different, slower concern that belongs
against a real engine — module 10 runs the real migrations against Testcontainers
Postgres.

## Exercise

```bash
make ex M=09
```

## You should now be able to

- Explain why `join_transaction_mode="create_savepoint"` alone doesn't isolate tests
  against SQLite, and what fixes it.
- Recognize a pytest-asyncio `ScopeMismatch` error and fix it with the right
  `loop_scope`.
- Write a test proving real transactional rollback (multiple lines, partial
  reservation, full rollback) that a hand-rolled fake (module 05) cannot prove.
- Explain the SQLite/Postgres split this repo uses and why `with_for_update()`
  needs a real database to test honestly (module 10 finishes this thread).

## References

- SQLAlchemy docs, "Joining a Session into an External Transaction (such as for test
  suites)" — https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
- SQLAlchemy docs, SQLite dialect notes on pysqlite transactional DDL —
  https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
- pytest-asyncio docs, configuration reference (`loop_scope`, the default-scope ini
  options) — https://pytest-asyncio.readthedocs.io/en/latest/reference/configuration.html
