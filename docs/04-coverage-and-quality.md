# 4. Coverage and test quality

## Line, branch, and why this repo enables branch coverage

**Line coverage** just asks "did this line execute at least once." It's trivially
gameable: `if x: do_a()` gets "100% line coverage" from a single test even if
`do_a()` never runs, because the `if` line itself executed either way.

**Branch coverage** asks "did each branch (`if` true *and* false, each `except`,
each boolean short-circuit) execute." This repo's `pyproject.toml` sets
`branch = true` under `[tool.coverage.run]` for exactly this reason — see module 12.

Coverage, even branch coverage, only tells you code *ran*, never that it ran
*correctly*: a test with no assertions gets full credit. Coverage is a floor ("we
definitely have zero tests for this branch") not a target ("100% coverage means the
code is correct"). Goodhart's Law bites hard here — the moment coverage % becomes
the metric a team is graded on, people write assertion-free tests to satisfy it.

**Example** (checked with `coverage --branch`):

```python
def apply_discount(price, is_member):
    if is_member:
        price = price * 0.9
    return price

def test_member_gets_10_percent_off():
    assert apply_discount(100, True) == 90
```

Line coverage: **100%** — every line ran. Branch coverage: **not 100%** — the report
flags `15->17`: the path where `is_member` is false was never taken. If someone later
breaks non-members' prices, no test notices.

## Mutation testing: testing your tests

If coverage can't tell you whether your assertions are any good, what can? Mutation
testing: a tool automatically introduces small bugs into your code (flip a `<` to
`<=`, change a `+` to `-`) and reruns your suite. If the suite still passes, that
mutant "survived" — meaning no test would have caught that specific bug. A high
mutation-kill-rate is a much stronger signal than high coverage. Not built out as a
module in this repo (it's slow and most valuable once a suite is already mature),
but `mutmut` is the standard Python tool — see `07-resources.md`.

**Example.** The mutation tool changes `if is_member:` to `if True:` and reruns the
tests above. `test_member_gets_10_percent_off` still passes, so that mutant
**survived** — proof that nothing tests non-members. Add
`assert apply_discount(100, False) == 100` and the mutant is now killed. Mutating
`0.9` to `0.8` would already have been killed by the existing test; the *surviving*
mutants are what point at the gaps.

## Test smells

Recognizable patterns that predict a test suite will become a liability:

- **Fragile test** — breaks on any refactor, even behavior-preserving ones (usually:
  over-mocking, or asserting on private/internal state). See `02-test-doubles.md`.
- **Mystery guest** — the test depends on external state (a file, a DB row) that
  isn't visible in the test itself, so a reader can't tell why it should pass.
- **Test interdependence** — test B only passes if test A ran first and left state
  behind. Breaks FIRST's "Independent," and breaks under `pytest-randomly` or
  `pytest-xdist` — which is exactly why module 00 turns randomized ordering on early.
- **Excessive setup** — twenty lines of Arrange for one line of Assert usually means
  either the unit under test has too many dependencies, or a fixture/factory should
  exist to hide the noise (module 03).
- **Assertion roulette** — many assertions with no messages in one test; when it
  fails, you can't tell which assertion did it without re-running in verbose mode.
- **Slow test in the wrong tier** — an "integration" test that could have been a
  fast unit test with a fake, dragging down the whole suite's feedback loop.

**Two smells in code:**

```python
# Assertion roulette: which of these failed? You must re-run to find out.
def test_order():
    assert o.status == "paid"
    assert o.total == 2200
    assert o.lines[0].qty == 2
    assert o.payment_ref
    assert o.created_at

# Mystery guest: where does user 42 come from? Some fixture file, somewhere.
def test_user_can_checkout():
    assert checkout(user_id=42).ok
```

Fixes: split into focused tests (or add messages), and create the data the test
depends on *inside* the test or a visible fixture.

## Flakiness

A flaky test passes and fails on the same code, nondeterministically. It's worse
than no test: people learn to re-run CI instead of investigating, and eventually
stop trusting *any* red build. Common causes, and this repo's countermeasures:

- **Shared/leaked state between tests** — module 09's transaction-rollback-per-test
  pattern exists specifically so DB tests can't leak rows into each other.
- **Real, uncontrolled time** — `Clock` (module 07) and `freezegun` remove
  wall-clock time as a variable.
- **Test order dependence** — `pytest-randomly` (on by default here) surfaces this
  early by shuffling order every run, instead of letting you get lucky in CI for
  months and then fail mysteriously.
- **Unawaited concurrency / real network calls** — module 08's respx tests remove
  the real network as a variable for gateway tests; module 10's Testcontainers tests
  accept realism deliberately, and pay for it with tighter fixture-scoping discipline.
- **Resource exhaustion under parallel runs** (`pytest-xdist`) — not built out as its
  own module here, but the general fix is the same one as above: no shared mutable
  state between tests, full stop.

> Fowler, "Eradicating Non-Determinism in Tests" —
> <https://martinfowler.com/articles/nonDeterminism.html> — is the canonical reference
> and worth reading end to end once you've hit your first real flaky test.

**Flaky tests, by cause:**

```python
# 1. Real time
assert order.created_at.date() == date.today()       # fails if run at 23:59:59.9

# 2. Shared state / order dependence
_seen = set()
def test_registers_user():  assert register("bob") and "bob" in _seen   # fails on rerun

# 3. Real timing
await asyncio.sleep(0.1); assert job.done                              # fails on a slow CI box
```

Fixes: inject a fixed clock (module 07); give every test its own state (module 03,
module 09's rollback); wait on the *condition* (`await job.wait()`), never on a guess
about duration.

## Next

- `05-backend-testing-playbook.md` — applying all of this to a layered backend
- `modules/12-coverage-and-hypothesis`
