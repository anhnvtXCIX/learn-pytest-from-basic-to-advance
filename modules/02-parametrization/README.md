# 02. Parametrization

Turning `docs/03-what-to-test.md`'s equivalence-partitioning and boundary-value
techniques into runnable pytest, without copy-pasting the test body per case.

## The basics

```python
@pytest.mark.parametrize("subtotal_cents,expected_discount", [
    (4_999, 0),
    (5_000, 250),
])
def test_discount(subtotal_cents, expected_discount):
    assert calculate_discount_cents(subtotal_cents) == expected_discount
```

Each tuple becomes one independent test (own pass/fail, own line in `-v` output).
Comma-separated argument names as one string, or a list/tuple of names, both work;
prefer the string form for two or three names, a tuple for more (it's more
`black`/`ruff format`-friendly).

## `ids`: naming your cases

By default pytest derives an id from the parameter values (`test_discount[4999-0]`),
which gets unreadable fast for non-trivial values. Give explicit ids:

```python
@pytest.mark.parametrize(
    "subtotal_cents,expected_discount",
    [(4_999, 0), (5_000, 250)],
    ids=["below_lowest_tier", "at_lowest_tier_boundary"],
)
```

A good id names the *scenario*, not the values — `at_lowest_tier_boundary` survives
you later changing the threshold from 5,000 to 6,000; `subtotal_5000` doesn't.

## Stacking parametrize decorators

Two (or more) `@pytest.mark.parametrize` decorators on one test multiply: pytest runs
the *cross product* of both sets of values. Useful when two inputs vary independently
and you genuinely want every combination — be deliberate about this, since N x M
cases arrive fast, and a decision-table case (`docs/03`) is usually better expressed
as one parametrize with explicit tuples than as a cross product that includes
combinations you don't actually care about.

## `pytest.param(..., marks=..., id=...)`

Wrap an individual case to attach a marker or a custom id to just that one entry:

```python
pytest.param(0, 0, marks=pytest.mark.xfail(reason="zero lines should raise, not return 0"), id="empty_order"),
```

## Indirect parametrization

Normally parametrized values go straight into the test function. With
`indirect=True`, they go into a *fixture* instead (via `request.param`), so the
fixture can do setup work based on the parameter before the test sees the result.
Use this when "building the thing to test" is itself nontrivial per-case (see the
example: building a repository already pre-loaded with different stock levels).

## `pytest_generate_tests`

A hook (defined in `conftest.py`) for generating parametrize cases *programmatically*
— e.g. deriving every boundary from `DISCOUNT_TIERS` itself so the test suite can't
silently drift out of sync with the tiers table if someone adds a fourth tier. Prefer
plain `@pytest.mark.parametrize` until you have a concrete reason (generating from a
data source, deriving cases from another table) to reach for this hook — it's more
powerful and more indirect, which is a worse default.

## Exercise

```bash
make ex M=02
```

## You should now be able to

- Parametrize a test with explicit, meaningful `ids`.
- Explain what stacking two `@parametrize` decorators actually produces.
- Use `pytest.param(marks=...)` to mark one case `xfail` without affecting the rest.
- Recognize when `indirect=True` or `pytest_generate_tests` are the right tool
  instead of plain parametrize.

## References

- pytest docs, "How to parametrize fixtures and test functions" —
  https://docs.pytest.org/en/stable/how-to/parametrize.html
- pytest docs, `pytest_generate_tests` —
  https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_generate_tests
