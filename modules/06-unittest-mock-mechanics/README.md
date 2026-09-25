# 06. `unittest.mock` mechanics

Module 05 built doubles by hand to learn the taxonomy. This module is the standard
library tool that does most of that job for you -- and its sharp edges.

## `Mock`, `MagicMock`, `AsyncMock`

- `Mock()` — anything you don't call is fine; any attribute access or call
  auto-creates a child `Mock`. This is *convenient and dangerous*: `mock.charge` and
  `mock.chrage` (typo) both silently succeed, returning yet another `Mock`. See
  autospec below for the fix.
- `MagicMock()` — a `Mock` that also implements Python's dunder/magic methods
  (`__len__`, `__iter__`, `__enter__`, ...), so it works where plain `Mock` would
  raise `TypeError` for things like `len(mock)`.
- `AsyncMock()` — like `MagicMock`, but calling it returns a coroutine, so `await
  mock()` works. **This matters a lot in this repo**: every gateway/repository
  method here is `async def`. If you use a plain `Mock`/`MagicMock` for an async
  method, calling it returns a `Mock` (or `MagicMock`) object, not a coroutine, and
  `await`ing that raises `TypeError: object Mock can't be used in 'await'
  expression` — a confusing error if you don't immediately recognize the cause.
  `Mock(spec=...)` and `create_autospec(...)` correctly infer `AsyncMock` for
  methods that are actually `async def` on the spec'd object, which is one more
  reason to prefer autospec over a bare `Mock`.

## Call assertions

`mock.assert_called_once_with(...)`, `mock.call_count`, `mock.call_args`,
`mock.call_args_list` — the spy-style checks from module 05, built in.
`AsyncMock` adds await-aware equivalents: `assert_awaited_once_with(...)`,
`await_count`. Prefer the `_awaited_` family for async mocks — it fails with a
clearer message if the mock was *called* (e.g. someone forgot `await`) but never
actually awaited.

## `side_effect`

Set to an **exception** to make the mock raise instead of return:
```python
mock_gateway.charge.side_effect = PaymentGatewayUnavailableError("timed out")
```
Set to a **callable** to compute a return value (or raise) from the actual call
arguments — for when a canned `return_value` isn't expressive enough. Set to an
**iterable** to return a different value on each successive call (first call
succeeds, second raises, etc.) — useful for testing retry logic, though
`OrderService` in this repo doesn't retry (see module 08's README for why that's a
deliberate choice, not an oversight).

## "Where to patch": the single most common `unittest.mock` bug

`unittest.mock.patch(target)` replaces a name **in the namespace where it's looked
up at call time**, not where it's originally defined. If module `service.py` does
`from greeter import get_greeting`, then `service` now has its *own* reference to
that function in its own namespace — patching `greeter.get_greeting` afterward does
nothing to `service`'s already-bound reference. You must patch
`"service.get_greeting"` (where it's *used*), not `"greeter.get_greeting"` (where
it's *defined*). `examples/test_where_to_patch.py` proves both halves of this with a
real, isolated pytest run (via `pytester`) rather than asserting it in prose.

This entire class of bug is *why this repo prefers dependency injection over
patching* everywhere it reasonably can (`PaymentGateway` as a constructor argument,
not an import reached into at call time) — see `docs/02-test-doubles.md`'s "don't
mock what you don't own." When you do need to mock something you don't control
directly (a third-party client library, module 08's `httpx`), knowing this rule is
what keeps the mock from silently mocking nothing.

## `autospec` / `create_autospec` / `spec_set`

```python
from unittest.mock import create_autospec
mock_gateway = create_autospec(HttpPaymentGateway, instance=True)
```

`create_autospec` inspects the real class and builds a mock whose attributes and
call signatures are *constrained to match it*: `mock_gateway.charge(amonut_cents=1)`
(typo) raises `AttributeError` immediately, and
`mock_gateway.charge(nonexistent_kwarg=1)` raises `TypeError` for a bad signature —
both would silently succeed on a bare `Mock()`. `spec_set=True` additionally
prevents *setting* an attribute that doesn't exist on the real object (catches typos
in test setup, not just in calls). Prefer autospec any time you're mocking a real
class rather than a `Protocol` you already fully control — for this repo's
`Protocol`-based seams (`PaymentGateway`, `IdempotencyLock`), a hand-rolled fake
(module 05) is often clearer anyway, but for third-party classes (`httpx.AsyncClient`)
autospec is close to essential.

## `pytest-mock`'s `mocker` fixture

Same `unittest.mock` machinery, nicer ergonomics: `mocker.patch(...)` instead of a
`with patch(...):` block or a `@patch(...)` decorator, and pytest-mock
**automatically undoes every patch at the end of the test**, even if the test fails
— no `try/finally` needed, and no risk of a forgotten `patch.stop()` leaking into the
next test. Prefer `mocker.patch` over raw `unittest.mock.patch` in this repo's tests.

## Exercise

```bash
make ex M=06
```

## You should now be able to

- Explain why an async method needs `AsyncMock`, not `Mock`/`MagicMock`, and
  recognize the `TypeError` that shows up when you get it wrong.
- State the "where to patch" rule from memory and apply it correctly.
- Use `create_autospec` and explain what it protects against that a bare `Mock`
  doesn't.
- Use `side_effect` to make a mock raise, and to return different values across
  calls.
- Prefer `mocker.patch` over raw `unittest.mock.patch` and say why.

## References

- `unittest.mock` docs — https://docs.python.org/3/library/unittest.mock.html
- `unittest.mock`, "Where to patch" —
  https://docs.python.org/3/library/unittest.mock.html#where-to-patch
- `unittest.mock`, `autospec` — https://docs.python.org/3/library/unittest.mock.html#autospeccing
- pytest-mock docs — https://pytest-mock.readthedocs.io/en/latest/usage.html
