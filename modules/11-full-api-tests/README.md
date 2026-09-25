# 11. Full API tests

The top of this repo's testing pyramid: real HTTP routing (via
`httpx.AsyncClient` + `ASGITransport`, no real network socket), a real database
(module 09's fast SQLite tier), and exactly one fake (the payment gateway --
module 05's fakes, wired in via module 07's `dependency_overrides`). Building this
module's examples found three real bugs — read on.

## The harness (`examples/conftest.py`)

`app` builds the real `create_app()` and overrides `get_order_service` with an
`OrderService` wired to a real `UnitOfWork` (bound to the same rollback-per-test
`sessionmaker` as module 09) and fakes for the gateway/lock/clock. `client` wraps it
in an `httpx.AsyncClient`. `seeded_product` uses `polyfactory`'s `DataclassFactory`
to build a valid `Product` with only the fields a given test cares about overridden
— the factory pattern module 03 built by hand, generalized.

## Bug found #1: a genuinely deprecated stdlib-adjacent constant

Building this module's error-path tests immediately failed with:

```
StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated.
Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
```

promoted to a hard error by this repo's `filterwarnings = ["error"]`. This was a
real bug in `src/shop/api/routes.py` (now fixed), caught by the tests, exactly as
the strict warnings config is supposed to work — not a lesson invented for this
module, an actual thing this repo's own tests found and fixed.

## Bug found #2: the closure-capture mistake in `dependency_overrides`

`app.dependency_overrides[get_order_service] = lambda: OrderService(...)` — FastAPI
calls that lambda **fresh, on every single request** that depends on
`get_order_service`. Building `test_concurrent_duplicate_requests_only_one_wins`,
the first version constructed `FakeIdempotencyLock()` *inside* the lambda — meaning
each of the two "concurrent" requests silently got its own, unshared lock instance,
which never actually contended with anything, which surfaced as a
`UNIQUE constraint failed: orders.idempotency_key` database error instead of the
expected `409`. The fix: build `fake_lock` (and `fake_gateway`) **once**, outside
the lambda, and capture them by closure. See
`examples/test_full_order_flow.py`'s comment on that test for the full story — this
is a real, easy mistake to make with `dependency_overrides` specifically because the
lambda syntax makes "build a fresh one each time" look identical to "share one."

## Bug found #3: concurrency tests can't share the rollback-per-test connection

The same test's *second* problem, hit right after fixing the first: running two
concurrent requests against the module's shared `client`/`sessionmaker` fixtures
corrupted the SAVEPOINT stack (`OperationalError: no such savepoint`, or
SQLAlchemy's `nested transaction already deassociated from connection`) — the exact
failure mode module 10's `test_concurrency.py` docstring warns about, hit here for a
second, independent time. `sessionmaker` (module 09's pattern) binds every session
to ONE shared connection specifically so a single test's writes roll back cleanly;
two concurrent requests both opening/closing SAVEPOINTs on that one connection at
the same time is exactly what it can't survive. The fix, in
`test_concurrent_duplicate_requests_only_one_wins`: build a **dedicated**, real,
pooled engine against an on-disk SQLite file in `tmp_path` (module 03) — not
`:memory:`, which is private to a single connection and can't be shared across a
pool the way concurrent requests need — just for that one test, bypassing the
module's shared fixtures entirely.

**The general lesson underneath all of this:** a fixture built for one purpose
(fast, isolated, rolled-back single-test writes) is not automatically safe to reuse
for a different purpose (genuine concurrent access) just because it's convenient and
already there. Read what a fixture's isolation mechanism actually does before
reaching for it in a new kind of test.

## Data builders: `polyfactory`

```python
class ProductFactory(DataclassFactory[Product]):
    __model__ = Product

ProductFactory.build(unit_price_cents=1_500, stock_qty=5)
```

Every field not overridden gets a random-but-type-correct value. This is module 03's
hand-rolled factory-as-fixture pattern, generalized to any dataclass without writing
the builder function yourself — and, like the hand-rolled version, the point is
still to make each test's *override* the only thing a reader has to look at.

## Exercise

```bash
make ex M=11
```

## You should now be able to

- Wire a full FastAPI + real-DB + faked-external-service test harness using
  `dependency_overrides`.
- Recognize the "lambda captures a fresh fake per call" mistake and avoid it.
- Explain why a rollback-per-test fixture is the wrong tool for a genuine
  concurrency test, and what real fix that implies.
- Use `polyfactory` to build valid-by-default test data with targeted overrides.

## References

- FastAPI docs, testing — https://fastapi.tiangolo.com/tutorial/testing/
- FastAPI docs, "Testing Dependencies with Overrides" —
  https://fastapi.tiangolo.com/advanced/testing-dependencies/
- polyfactory docs — https://polyfactory.litestar.dev/
