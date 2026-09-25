# 07. Choosing a seam

A "seam" (Michael Feathers' term, *Working Effectively with Legacy Code*) is a place
in the code where you can change behavior without editing the code itself. Every
technique below is a different way to substitute something at a seam. The skill this
module builds isn't any one technique — it's choosing the *right* one for a given
situation.

## The options, ranked by preference

1. **Dependency injection** — the collaborator is a constructor/function argument.
   No patching machinery needed at all; you just pass a different object. This
   repo's `Clock`, `PaymentGateway`, and `IdempotencyLock` protocols exist so
   `OrderService` can be tested this way (module 05). Prefer this whenever you're
   writing the code being tested — it's simpler, faster, and immune to the "where to
   patch" class of bug entirely.
2. **`monkeypatch`** (pytest built-in) — for global/module state you don't control
   the construction of: environment variables, `sys.path`, an attribute on a module
   or class. Auto-undoes at the end of the test, like `mocker.patch`, but with a
   simpler API and no call-tracking (it's not a spy — if you also need to assert on
   calls, reach for `mocker.patch` instead, which gives you a `Mock` back).
3. **`mocker.patch` / `unittest.mock.patch`** — module 06's territory. Use when you
   need call assertions on something you don't own and can't inject.
4. **A purpose-built library** (`freezegun`, `respx`) — for popular, painful special
   cases where hand-rolling the patch is either extremely fiddly or outright
   impossible. Time is the standout example, next.

## Why time needs a special-case library

Try monkeypatching `datetime.datetime.now` directly:

```pycon
>>> from datetime import datetime
>>> datetime.now = lambda: "patched"
TypeError: cannot set 'now' attribute of immutable type 'datetime.datetime'
```

`datetime.datetime` is implemented in C and immutable — you cannot attach a
monkeypatch to it directly, full stop (verified above, not a guess). This is
*specifically* why `freezegun` exists: it does something lower-level than a normal
monkeypatch to make `datetime.now()`, `time.time()`, etc. return a fixed value
everywhere in the process for the duration of a `with freeze_time(...):` block —
including inside code that calls the real stdlib directly, which is exactly the case
a normal patch can't reach. See `examples/test_freezegun.py`.

**Prefer dependency injection (this repo's `Clock`) for code you're writing.**
Reach for `freezegun` specifically for code that calls `datetime.now()` directly and
that you don't want to (or can't) refactor to accept an injected clock — third-party
code, or a huge existing codebase where introducing DI everywhere isn't realistic
today.

## Controlling randomness

Same principle, an extra wrinkle specific to this repo: `docs/04-coverage-and-quality.md`'s
module 03 aside already found that **`pytest-randomly` reseeds Python's global
`random` state immediately before every test's call phase**, which silently defeats
a fixture that tries to `random.seed(...)` during setup. If your code calls
`random.random()` (or similar) directly, don't try to control it via seeding in a
fixture in this repo — inject a `random.Random` instance (or a small `Protocol`, the
same pattern as `Clock`) instead, and give the test a fixed one. See
`examples/test_controlling_randomness.py` for both the seeding trap and the DI fix,
side by side.

## Environment variables: `monkeypatch.setenv`

`Settings` (`src/shop/config.py`) reads environment variables *once*, when
instantiated. `monkeypatch.setenv("SHOP_TAX_RATE", "0.20")` followed by constructing
a *fresh* `Settings()` picks it up; monkeypatching the environment does nothing to a
`Settings` instance that already exists. See `examples/test_settings_env.py`.

## FastAPI's `dependency_overrides`: DI at the HTTP layer

FastAPI's own dependency injection system (`Depends(...)`) has a built-in override
mechanism for tests: `app.dependency_overrides[get_order_service] = lambda: fake_service`
replaces the real dependency for every request made against that `app` instance,
without touching any import path. This is the API-layer equivalent of constructor
injection, and it's the seam module 11's full API tests are built on. See
`examples/test_dependency_overrides.py` for a minimal version; module 11 uses it at
full scale.

## Exercise

```bash
make ex M=07
```

## You should now be able to

- Rank DI, `monkeypatch`, and `mocker.patch` by preference and explain why.
- Explain why `datetime.now` can't be monkeypatched directly and what `freezegun`
  does differently.
- Explain the pytest-randomly reseeding trap from module 03 and the DI-based fix.
- Use `app.dependency_overrides` to replace a FastAPI dependency in a test.

## References

- Michael Feathers, *Working Effectively with Legacy Code* — the source of "seam"
  as a testing term.
- pytest docs, `monkeypatch` — https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- freezegun docs — https://github.com/spulec/freezegun
- FastAPI docs, "Testing Dependencies with Overrides" —
  https://fastapi.tiangolo.com/advanced/testing-dependencies/
