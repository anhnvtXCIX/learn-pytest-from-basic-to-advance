# 5. A testing playbook for layered backends

The role-specific chapter. If you only read one doc file, read this one, then go
write code — everything here is illustrated by `src/shop` and exercised by the
modules cited inline.

> This whole approach — a domain layer with no I/O, repositories as the only thing
> that speaks to the database, a service layer that orchestrates via dependency
> injection — is essentially the architecture from Percival & Gregory,
> *Architecture Patterns with Python* (free): https://www.cosmicpython.com/book/preface.html.
> If this doc's shape resonates, that book is the deeper version of it.

## The layers, and what "testing" means at each one

| Layer | What it is here | What to test | How |
|---|---|---|---|
| `domain/` | Pure functions/dataclasses, no I/O | Every rule, every boundary, every invariant | Fast unit tests, parametrize, Hypothesis (modules 01-02, 12) |
| `db/` (repositories) | The only code that speaks SQLAlchemy | That queries do what you think against a *real* engine — constraints, locking, transactions | Integration tests, both SQLite and Postgres tiers (modules 09-10) |
| `gateways/` | Adapters to systems you don't own (HTTP, Redis) | Your adapter's request/response handling and error translation | respx for HTTP (module 08); fakes for unit tests, Testcontainers Redis for the real thing (module 10) |
| `services/` | Orchestration: calls the above in the right order, handles partial failure | The *orchestration logic itself* — call order, compensation, idempotency — independent of which backend is real | Every collaborator faked (modules 05-08), then re-run against real infra (modules 09-11) |
| `api/` | FastAPI routes: HTTP in, HTTP out | Status codes, JSON shape, auth, exception-to-HTTP mapping | `httpx.AsyncClient` + `ASGITransport`, `dependency_overrides` (modules 07, 11) |

The key habit this table is trying to build: **before writing a test, name which
layer's job you're checking.** A test that exercises the API layer, the service
layer, and a real database all at once, testing all of it "at the same time," makes
failures ambiguous and the suite slow. It's fine — often correct — to *also* have a
handful of true end-to-end tests (module 11's full-stack tests exist for exactly
this), but they should be a deliberate minority, not the default shape of every test.

## Database testing strategy: three ways to isolate a test

All three exist in real codebases; know the tradeoff.

1. **Transaction rollback per test** (module 09's default) — begin a transaction,
   run the test, roll it back, so nothing persists. Fast (no schema recreation), and
   fully isolates tests from each other. The catch: code under test that itself
   calls `commit()` (this repo's `UnitOfWork` does) can defeat naive rollback wrapping
   — module 09's README works through the specific fixture pattern that handles this
   for async SQLAlchemy.
2. **Truncate between tests** — let each test commit normally, then wipe all tables
   before the next test. Simpler to reason about with code that commits internally,
   slower than rollback at any real scale.
3. **Fresh database per test (or per session)** — recreate the schema per test
   (slow) or per session (module 10's Testcontainers Postgres: one container per test
   *session*, migrations run once, tests share it but each gets an isolated
   transaction/rollback on top).

**SQLite vs. a real engine.** SQLite-in-memory is excellent for the *inner loop* —
milliseconds per test, zero setup — but it silently diverges from Postgres in ways
that matter: `.with_for_update()` is a no-op (verified in this repo, see
`src/shop/db/repository.py`), constraint-violation exception types differ, and there
is no real JSONB. The rule this repo follows: SQLite for anything testing your
*query logic*; a real Postgres (via Testcontainers) for anything testing
*concurrency, constraints, or dialect-specific types*. Module 10 makes this concrete
with a test that passes against SQLite and is simply wrong, and the same test
against real Postgres catching a real race condition.

## Testing external services you don't control

Three options, in order of preference for *most* cases:

1. **A fake behind your own interface** (`PaymentGateway` protocol) — for testing
   your orchestration logic. Fast, no network, but only as correct as the fake's
   author made it.
2. **respx (or similar) at the HTTP transport level** — for testing your *adapter*
   code (`HttpPaymentGateway`): request shape, header/auth handling, response
   parsing, retry/timeout behavior. Still no real network call, but it exercises the
   real `httpx` code path instead of a Python-level stand-in. Module 08.
3. **The real sandbox/staging API** — for a *small* number of true contract tests,
   run less often (nightly, not on every commit) since third-party latency and
   quotas make them slow and occasionally flaky through no fault of your own. Not
   built out in this repo — see `07-resources.md` for schemathesis/Pact if you need
   this for real.

## Testing idempotency and concurrency

Two different concerns that often get conflated:

- **Idempotency** — calling an operation twice with the same key produces the same
  result as calling it once, with no double side effect (no double charge). Testable
  *sequentially*: call `place_order` twice with the same idempotency key, assert one
  order and one charge.
- **Concurrency correctness** — two *simultaneous* callers don't interleave badly
  (e.g. both reserve the last unit of stock). This genuinely requires real
  concurrency against a real lock-capable backend to test honestly — you cannot
  fake your way to a valid answer about whether a race condition exists. Module 10
  runs literal concurrent transactions against Testcontainers Postgres for this.

## Test data management

- Prefer **factories** (module 11 uses `polyfactory`) over fixture files for
  generating valid-by-default objects with overridable fields — a fixture file goes
  stale silently when the schema changes; a factory built from the actual dataclass
  fails loudly.
- Keep test data **minimal and intention-revealing**: a product built with
  `stock_qty=1` in a stock-exhaustion test should not also specify an irrelevant
  `sku` unless the test cares about it — every field a reader sees, they'll assume
  is relevant.
- Never depend on **auto-incrementing IDs** having a specific value across tests;
  capture the ID a fixture/factory actually returns.

## CI strategy

Fast, no-Docker unit+SQLite-integration tests on every push; the Testcontainers tier
gated the same way (still every push, since Docker is available in GitHub Actions,
just as a separate, cacheable job) so real-engine regressions aren't found a day
later. Coverage gate as a floor, not a target (`04-coverage-and-quality.md`). Module
14 builds this out concretely.

## Next

- `06-glossary.md` for quick lookups
- `07-resources.md` for the full reading list
- Start writing tests: `modules/00-getting-started`
