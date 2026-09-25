# 1. Testing fundamentals

Read this before module 00. It's the vocabulary and mental model the rest of the repo
assumes — pytest syntax is the easy 20%; knowing *what* to test and *why* is the part
that actually prevents production incidents.

## Why test at all

Tests exist to let you change code without re-verifying the whole system by hand
every time, and to let you verify a requirement without a human doing it manually.
Every test you write is a trade: time spent writing and maintaining it, against time
saved catching regressions and time saved during debugging (a failing unit test
points at a function; a bug report from production points at nothing). The trade is
usually excellent for logic-heavy code and gets progressively worse for
glue code, generated code, and code that's about to be deleted. Part of the skill is
knowing when *not* to write a test.

## The pyramid, the trophy, the honeycomb

The classic **test pyramid** (Mike Cohn, popularized further by Martin Fowler) says:
lots of fast, cheap unit tests at the base; fewer integration tests; fewer still
end-to-end tests at the top. The shape encodes a cost curve — unit tests are cheap
and fast but tell you less about whether the system actually works together;
end-to-end tests tell you the most but are slow, flaky, and expensive to maintain.

> Fowler, "TestPyramid" — https://martinfowler.com/bliki/TestPyramid.html

Kent C. Dodds later proposed the **testing trophy** for typical web apps: fewer pure
unit tests, a *large* integration layer, a thin end-to-end layer, plus static
analysis (types, linting) as a free base layer underneath everything. The argument:
for most CRUD-and-glue backend code, integration tests give the best confidence per
dollar, because so much of what breaks in production is exactly the *wiring* between
units that a unit test, by design, doesn't exercise.

> Dodds, "Write tests. Not too many. Mostly integration." —
> https://kentcdodds.com/blog/write-tests

Spotify's **honeycomb** model makes a similar point specifically for microservices:
integration-style tests dominate, because a service's job *is* talking to its
dependencies.

**Practical takeaway for this repo:** none of these shapes is "the truth" — they're
each a correction to a specific failure mode (all-E2E suites that take an hour and
flake constantly; all-unit suites that pass while the wired-together system is
broken). `docs/05-backend-testing-playbook.md` gives you a concrete per-layer rule
for *this* codebase's shape instead of a triangle to memorize.

## The test levels, precisely

These terms get used loosely; here's what this repo means by each one (see
`src/shop`'s layering for where each lives):

- **Unit test** — exercises one unit (usually one function or class) in isolation.
  "Isolation" is the contested word: a *solitary* unit test replaces every
  collaborator with a test double; a *sociable* unit test lets real collaborators run
  as long as they're fast and in-process (Meszaros' terms — see `02-test-doubles.md`).
  `domain/pricing.py` is a good example either way, because it *has* no collaborators.
- **Integration test** — exercises the interaction between your code and something
  it doesn't fully control: a database, the filesystem, another process. The
  definition this repo uses (and argues for in `05-backend-testing-playbook.md`):
  an integration test's job is to prove that the *boundary itself* behaves the way
  your code assumes it does. This is `modules/09-11`'s entire subject.
- **Contract test** — a narrower integration test that checks your assumptions about
  a boundary you don't control end-to-end, e.g. "does the payment gateway's API still
  return this JSON shape for a decline." Not built out in this repo (see
  `07-resources.md` for where to go next), but respx-based tests in module 08 are its
  cheaper cousin: they check *your side* of the assumption stays consistent.
- **End-to-end (E2E) test** — drives the whole deployed system as a user or external
  caller would, usually over the network, usually including things you don't own at
  all. Module 11's full API tests are "as close to E2E as this repo gets without a
  real deployed payment provider" — genuinely E2E would also hit the real payment
  sandbox, which is out of scope here.
- **Smoke test** — a shallow "did it even start" check, run after a deploy.
- **Regression test** — any test added *because* a bug happened, to make sure it
  can't happen silently again. Not a different kind of test technically — a note
  about *why* it exists.

## Structuring a test: AAA / Given-When-Then

Almost every good test has three parts, however they're spaced or commented:

- **Arrange** (Given) — build the inputs and the world the test needs.
- **Act** (When) — do the one thing under test.
- **Assert** (Then) — check the outcome.

One `Act` per test is the discipline worth keeping: multiple acts make it unclear
which action caused a failing assertion, and tempt you into asserting on
intermediate state instead of the thing you actually care about.

## FIRST

A widely-cited checklist (from *Clean Code*, credited to Tim Ottinger & Jeff Langr)
for what a *unit* test should be:

- **Fast** — milliseconds, not seconds; a slow unit suite gets skipped.
- **Independent** — no test depends on another test's side effects or run order.
- **Repeatable** — same result on your machine, CI, in any order, at 3am.
- **Self-validating** — pass/fail, no human reading log output to decide.
- **Timely** — written close to the code it tests, not months later.

Integration tests get to relax "Fast" somewhat, but never "Independent" or
"Repeatable" — a flaky or order-dependent integration test is worse than no test,
because it trains people to re-run CI instead of investigating. Module 09 covers the
concrete techniques (transaction rollback per test, fixture scoping) that keep
integration tests independent and repeatable despite touching real state.

## Naming tests

A test name is documentation that runs. `test_it_works` tells you nothing when it
fails at 2am. Prefer a name that states the scenario and the expected outcome:
`test_insufficient_stock_raises_before_charging_payment`. If you can't name it that
specifically, the test is probably checking too many things at once.

## What "behavior, not implementation" means in practice

A test coupled to implementation breaks every time you refactor, even when behavior
is unchanged — this is the single biggest cause of a test suite people learn to
ignore. Concretely: assert on `OrderService.place_order()`'s *return value and its
observable side effects* (what got charged, what status the order ended up in),
not on "was `_release_reservation` called" unless that call *is* the contract. See
`02-test-doubles.md` for how this same principle shapes when mocking is appropriate.

## Next

- `02-test-doubles.md` — the vocabulary for stubs/mocks/fakes and when to use each
- `03-what-to-test.md` — systematic techniques for choosing test cases
- `05-backend-testing-playbook.md` — how all of this maps onto a layered backend
