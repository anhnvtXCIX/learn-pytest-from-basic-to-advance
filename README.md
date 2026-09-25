# learn-pytest-from-basic-to-advance

A hands-on curriculum for pytest — basics through advanced mocking and integration
testing — built around one realistic backend service instead of toy examples.

**Who this is for:** a working backend engineer who knows Python but wants to get
genuinely good at testing, especially mocking and integration testing.

## Why this repo is shaped the way it is

Most pytest tutorials teach syntax against `add(a, b)`-style functions. That's fine
for learning decorators, but it can't teach you the actual hard part: *which*
collaborator to fake, *how* real a database test needs to be, or what a genuine race
condition looks like. So this repo has a real app instead — a small, deliberately
layered Orders service (`src/shop/`) with a database, an external payment gateway, a
Redis lock, and a clock — chosen specifically because its seams map onto real
decisions. See `src/shop/__init__.py` and `docs/05-backend-testing-playbook.md`.

Every module below pairs **theory** (a `README.md` with real references, not just
"here's the syntax") with **runnable code**: heavily-commented `examples/` you read
and run, `exercises/` with TODOs you complete yourself, and `solutions/` you diff
against — not read first.

## Before you start

```bash
make install   # uv sync + alembic upgrade head
make test      # confirm you're green (no Docker needed for this)
```

You'll need [uv](https://docs.astral.sh/uv/) and Python 3.13 (uv installs the
interpreter for you: `uv python install 3.13`). Module 10 additionally needs a
running Docker daemon; nothing else does.

## How to work through a module

```bash
cat modules/00-getting-started/README.md      # read the theory + references
$EDITOR modules/00-getting-started/examples/   # read and run the worked examples
make ex M=00                                    # do the exercises yourself
make sol M=00                                   # check against the reference solution
```

Read `docs/01-testing-fundamentals.md` through `docs/05-backend-testing-playbook.md`
before or alongside Part 0 — they're the vocabulary and mental model the modules
assume, and they're short.

## Syllabus

**Part 0 — Foundations**
| # | Module | Covers |
|---|---|---|
| 00 | [Getting started](modules/00-getting-started) | discovery, CLI flags, random test order |
| 01 | [Test anatomy & assertions](modules/01-anatomy-and-assertions) | `raises`, `approx`, `warns` |
| 02 | [Parametrization](modules/02-parametrization) | `parametrize`, `ids`, indirect, `pytest_generate_tests` |
| 03 | [Fixtures deep dive](modules/03-fixtures) | scopes, yield teardown, conftest layering, factories, `tmp_path` |
| 04 | [Markers, config, selection](modules/04-markers-and-config) | custom markers, skip/skipif, `xfail(strict=)` |

**Part 1 — Test doubles & mocking** *(weak spot #1)*
| # | Module | Covers |
|---|---|---|
| 05 | [Test double taxonomy](modules/05-test-double-taxonomy) | dummy/stub/spy/fake/mock, the same test five ways |
| 06 | [`unittest.mock` mechanics](modules/06-unittest-mock-mechanics) | `Mock`/`AsyncMock`, "where to patch", `autospec` |
| 07 | [Choosing a seam](modules/07-choosing-a-seam) | DI vs `monkeypatch` vs `patch`, `freezegun`, `dependency_overrides` |
| 08 | [Mocking HTTP with respx](modules/08-mocking-http-with-respx) | route matching, timeouts/5xx, respx vs a mocked client |

**Part 2 — Integration testing** *(weak spot #2)*
| # | Module | Covers |
|---|---|---|
| 09 | [Integration foundations](modules/09-integration-foundations) | transaction-rollback-per-test, async loop-scope pitfalls |
| 10 | [Real infra with Testcontainers](modules/10-testcontainers) | real Postgres/Redis, real race conditions, dialect divergence |
| 11 | [Full API tests](modules/11-full-api-tests) | `httpx` + `ASGITransport`, `polyfactory`, idempotency & concurrency |

**Part 3 — Advanced**
| # | Module | Covers |
|---|---|---|
| 12 | [Coverage & Hypothesis](modules/12-coverage-and-hypothesis) | branch coverage, property-based & stateful testing |
| 13 | [Writing a pytest plugin](modules/13-pytest-plugins) | `pytest_addoption`, hook ordering, `testkit/` |
| 14 | [CI](modules/14-ci) | GitHub Actions, coverage gates, JUnit XML |

## The app under test

```
src/shop/
  domain/     pure Python: models, pricing, errors -- no I/O
  db/         SQLAlchemy: tables, repositories, Unit of Work
  gateways/   adapters to things we don't own: HTTP payments, Redis
  services/   orchestration: OrderService
  api/        FastAPI: routes, schemas, dependency injection
```

Each layer has a different testing story — see `docs/05-backend-testing-playbook.md`
for the full breakdown of what to test where and how.

## Software testing theory (`docs/`)

Not pytest-specific — this is the vocabulary and reasoning that transfers to any
language or framework:

1. [Testing fundamentals](docs/01-testing-fundamentals.md) — pyramid/trophy, AAA, FIRST
2. [Test doubles](docs/02-test-doubles.md) — the taxonomy, classicist vs. mockist
3. [What to test](docs/03-what-to-test.md) — equivalence classes, boundaries, decision tables
4. [Coverage & quality](docs/04-coverage-and-quality.md) — branch coverage, mutation testing, test smells
5. [Backend testing playbook](docs/05-backend-testing-playbook.md) — the role-specific synthesis
6. [Glossary](docs/06-glossary.md)
7. [Resources](docs/07-resources.md) — the full reading list, all primary sources

## What's real in here

Every technical claim in this repo — a library's behavior, a version number, a
gotcha — was checked against current docs or verified by actually running it while
this repo was built, not recalled from memory. Several modules document a real bug
that surfaced during that process (a deprecated Starlette constant, a Postgres
connection-pooling issue, an async loop-scope mismatch) and how it was found and
fixed, because that debugging process *is* the skill this repo is trying to teach.
See `CLAUDE.md` for repo conventions if you're extending this yourself.
