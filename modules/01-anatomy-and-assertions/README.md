# 01. Test anatomy & assertions

## `pytest.raises`

The standard way to assert that code raises an exception:

```python
with pytest.raises(InsufficientStockError):
    ...
```

Two refinements you'll use constantly:

- **`match=`** — a regex checked against `str(exception)`. Use it to pin down *which*
  error, not just that *an* error of the right type happened (two different bugs can
  both raise `InvalidOrderError`; `match` distinguishes them).
- **`as excinfo`** — capture the `ExceptionInfo` to assert on the exception's
  *attributes*, not just its message. This repo's domain exceptions carry structured
  data specifically so tests can do this instead of regex-matching a message string
  that might get reworded later: `excinfo.value.requested`, `excinfo.value.available`.

Prefer attribute assertions over `match=` when the exception has structured data —
messages are for humans and change; attributes are part of the contract.

**Common mistake:** putting too much code inside the `with pytest.raises(...):` block.
If three lines could each raise the exception, you don't know which one actually did.
Keep the block to the single call under test.

## `pytest.approx`

Floating-point equality is almost never exact (`0.1 + 0.2 != 0.3`). For any float
comparison, wrap the expected side: `assert result == pytest.approx(3.3)`. It accepts
`rel=` and `abs=` tolerances if the default (a small relative tolerance) isn't right
for your scale. This repo's money math avoids floats entirely (`domain/pricing.py`
uses integer cents), so you'll see `approx` here applied to the *rate* side of
things (e.g. converting a `tax_rate` to a percentage for a report) rather than to
money itself — which is itself a small lesson: reach for `approx` as a signal that
you're in genuinely float territory, not as a substitute for fixing an integer/float
mismatch that shouldn't exist.

## `pytest.warns`

Analogous to `raises`, but for `warnings.warn(...)`. Useful for testing deprecation
paths: "calling this old function still works, but warns." Same `match=` support.

## Exercise

```bash
make ex M=01
```

## You should now be able to

- Write a `pytest.raises` block that checks both the exception type and a specific
  attribute on it.
- Explain when `match=` is the right tool vs. when asserting an attribute is better.
- Use `pytest.approx` and say why it's necessary for float comparisons.

## References

- pytest docs, "Assertions about expected exceptions" —
  https://docs.pytest.org/en/stable/how-to/assert.html#assertions-about-expected-exceptions
- pytest docs, `approx` API — https://docs.pytest.org/en/stable/reference/reference.html#pytest-approx
- pytest docs, "Warnings" — https://docs.pytest.org/en/stable/how-to/capture-warnings.html
