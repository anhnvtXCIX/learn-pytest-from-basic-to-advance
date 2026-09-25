# 7. Resources

Every entry here is either a primary doc/changelog or a well-known, durable
reference. Version numbers below were current as of this repo's creation
(late September 2026) — pytest 9.1, pytest-asyncio 1.4, SQLAlchemy 2.1.

## Books

- Brian Okken, *Python Testing with pytest* (2nd ed., Pragmatic Bookshelf) — the
  single best pytest-specific book; this repo's modules 00-04 cover much of the same
  ground with a different worked example.
- Harry Percival & Bob Gregory, *Architecture Patterns with Python* — free at
  https://www.cosmicpython.com/book/preface.html. The Repository/Unit-of-Work/Service
  Layer architecture `src/shop` uses is straight from this book. Read chapters 1-6
  after finishing module 09 if the shape of `src/shop` interested you.
- Steve Freeman & Nat Pryce, *Growing Object-Oriented Software, Guided by Tests* —
  the canonical "London school"/mockist reference (`docs/02-test-doubles.md`).
- Titus Winters, Tom Manshreck, Hyrum Wright (eds.), *Software Engineering at
  Google* — chapters 11-14 (on testing) are free online:
  https://abseil.io/resources/swe-book/html/toc.html. Larger-scale-org perspective on
  flaky tests, test sizes, and the "test behavior not implementation" argument.
- Gerard Meszaros, *xUnit Test Patterns* — the test-double taxonomy's origin; the
  companion site is free: http://xunitpatterns.com/.

## Articles (short, high-value, free)

- Martin Fowler, "TestPyramid" — https://martinfowler.com/bliki/TestPyramid.html
- Martin Fowler, "Mocks Aren't Stubs" — https://martinfowler.com/articles/mocksArentStubs.html
- Martin Fowler, "Eradicating Non-Determinism in Tests" —
  https://martinfowler.com/articles/nonDeterminism.html
- Kent C. Dodds, "Write tests. Not too many. Mostly integration." —
  https://kentcdodds.com/blog/write-tests
- Ham Vocke, "The Practical Test Pyramid" — https://martinfowler.com/articles/practical-test-pyramid.html
  (a longer, more implementation-focused companion to the TestPyramid bliki entry)

## Official docs (primary source — check these over any blog post, including
## anything this repo says, when a library's behavior actually matters)

- pytest — https://docs.pytest.org/en/stable/
- pytest-asyncio — https://pytest-asyncio.readthedocs.io/ (the `event_loop` fixture
  was **removed** in 1.0; if a tutorial you're reading mentions overriding
  `event_loop`, it predates that and is out of date — see module 09)
- unittest.mock — https://docs.python.org/3/library/unittest.mock.html
- pytest-mock — https://pytest-mock.readthedocs.io/
- respx — https://lundberg.github.io/respx/
- Hypothesis — https://hypothesis.readthedocs.io/
- Testcontainers for Python — https://testcontainers-python.readthedocs.io/
- SQLAlchemy 2.0-style ORM — https://docs.sqlalchemy.org/en/20/orm/
- SQLAlchemy asyncio extension — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- polyfactory — https://polyfactory.litestar.dev/
- FastAPI testing guide — https://fastapi.tiangolo.com/tutorial/testing/
- coverage.py — https://coverage.readthedocs.io/

## Tools mentioned but not built out as a module here

Worth knowing exist once you've finished this repo:

- **pytest-xdist** — parallel test execution (`pytest -n auto`). The main new
  failure mode it introduces is tests that assumed they had the database/filesystem
  to themselves; everything in module 09 about isolation is what makes a suite
  xdist-safe.
- **mutmut** — mutation testing for Python (`04-coverage-and-quality.md`).
- **schemathesis** — property-based testing *of an API* directly from its OpenAPI
  schema; a natural next step after module 12's Hypothesis module if you own the API
  and want to fuzz your own contract.
- **Pact** — consumer-driven contract testing between services, for when "does my
  mock match what the real service does" needs to be continuously verified between
  two teams' CI pipelines rather than assumed.
- **factory_boy** — the more established, sync-first cousin of `polyfactory`; worth
  knowing if you land in a codebase that already uses it.
