# 12. Coverage done right, and property-based testing

Two unrelated-sounding topics that actually answer the same question from opposite
directions: "how do I know my tests are any good?" Coverage tells you what code ran
at all; Hypothesis tells you whether your assertions hold for inputs you'd never
have thought to write by hand.

## Coverage: branch, not line

`pyproject.toml` sets `branch = true` under `[tool.coverage.run]`. Line coverage
answers "did this line execute"; branch coverage answers "did each branch of an
`if`/`except`/boolean expression execute, in **both** directions." A single test
calling a function with `if x: do_a()` gives 100% *line* coverage without ever
exercising the `x` being falsy — branch coverage catches that a whole path was never
tested.

```bash
make cov   # terminal report + htmlcov/index.html
```

Read `htmlcov/index.html` after running it once — the red/yellow highlighting on
actual source lines is far more useful for finding gaps than the summary percentage.

## `# pragma: no cover`

For code that's genuinely untestable or intentionally unreachable (a defensive
`assert` that documents an invariant rather than handling a real runtime case) --
see `src/shop/db/uow.py`'s `assert self._session is not None` lines, which exist to
satisfy type checkers and to fail loudly if this class is ever misused internally,
not because that path is expected to run. Excluding a handful of such lines,
explicitly and by name, keeps the coverage number meaningful; excluding them by
routinely reaching for the pragma to silence a real gap defeats the entire point —
see `docs/04-coverage-and-quality.md`'s Goodhart's Law warning.

## Why 100% coverage is not the goal

Coverage tells you code *ran*. It says nothing about whether the test that ran it
*asserted anything meaningful*. `docs/04-coverage-and-quality.md` covers this at
length, and mutation testing (also covered there) as the actual answer to "are my
assertions any good." Treat this repo's coverage gate (module 14's CI) as a floor
that catches "we added a whole function with zero tests," not a target to chase to
100% by adding low-value tests.

## Hypothesis: testing properties, not examples

Every test so far has been example-based: pick specific inputs, assert specific
outputs. Hypothesis instead lets you state a **property** that should hold for
*any* valid input, and generates hundreds of inputs — including edge cases you
would never think to write by hand (`0`, negative numbers, huge numbers, empty
collections) — trying to break it.

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0))
def test_discount_never_exceeds_subtotal(subtotal_cents):
    assert calculate_discount_cents(subtotal_cents) <= subtotal_cents
```

`domain/pricing.py` is the ideal target: pure functions, no I/O, and real invariants
worth stating explicitly (`total == subtotal - discount + tax`, always;
`discount <= subtotal`, always). See `examples/test_pricing_properties.py`.

## `@example`: pinning a regression

When Hypothesis finds a failing case (it "shrinks" a large failing input down to the
smallest one that still fails, then reports it), add that exact case back as a
permanent, explicit example so it's checked on every run even if random generation
never happens to produce it again:

```python
@given(st.integers(min_value=0))
@example(0)  # the empty/zero case, worth pinning explicitly
def test_discount_never_exceeds_subtotal(subtotal_cents): ...
```

## Stateful testing

For something with a *sequence of operations* that must maintain an invariant
across all of them (not just per-call), `hypothesis.stateful.RuleBasedStateMachine`
generates random sequences of operations and checks the invariant after each one.
`examples/test_stateful_stock.py` models random reserve/release sequences against
module 05's `InMemoryProductRepository`, checking `stock_qty` never goes negative
and is conserved (nothing is created or destroyed) across any sequence Hypothesis
generates — a much stronger guarantee than the hand-picked sequences in earlier
modules' unit tests.

## Exercise

```bash
make ex M=12
```

## You should now be able to

- Explain the difference between line and branch coverage and why this repo enables
  branch coverage.
- Use `# pragma: no cover` narrowly and explain when it's appropriate.
- Write a Hypothesis property test with a strategy and an invariant assertion.
- Use `@example` to pin a specific regression case.
- Explain what a stateful test checks that a sequence of hand-written unit tests
  doesn't.

## References

- coverage.py docs, branch coverage — https://coverage.readthedocs.io/en/latest/branch.html
- Hypothesis docs — https://hypothesis.readthedocs.io/
- Hypothesis docs, stateful testing — https://hypothesis.readthedocs.io/en/latest/stateful.html
- `docs/04-coverage-and-quality.md`
