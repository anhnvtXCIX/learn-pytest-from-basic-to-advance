# 03. Fixtures deep dive

Fixtures are pytest's dependency-injection mechanism: a test declares what it needs
as a parameter name, and pytest supplies it by matching that name against a function
decorated `@pytest.fixture`. Everything else in this module is detail on top of that
one idea.

## Scopes

`@pytest.fixture(scope=...)` controls how often the fixture function actually runs:

- `function` (default) — once per test.
- `class` — once per test class.
- `module` — once per file.
- `package` — once per package (directory with an `__init__.py`; rare in this repo).
- `session` — once for the entire test run.

Wider scopes are a performance tool (an expensive setup, like a Testcontainers
Postgres in module 10, wants `session` scope) and a correctness risk in the same
breath: anything mutable shared across tests via a wide-scoped fixture can leak state
between them, which is exactly the "test interdependence" smell from
`docs/04-coverage-and-quality.md`. Default to `function` scope; widen deliberately,
and when you do, make sure what's shared is either immutable or reset between uses.

See `examples/test_fixture_scopes.py`, which makes reuse (or non-reuse) visible with
a counter, and try `uv run pytest examples/test_fixture_scopes.py --setup-show` to
see pytest print each fixture's setup/teardown as it happens.

## `yield` fixtures and teardown

```python
@pytest.fixture
def resource():
    thing = create_thing()
    yield thing
    thing.close()  # runs after the test, even if the test failed
```

Code after `yield` always runs (pytest treats it like a `finally`), which is why this
is the standard pattern for anything that needs cleanup — open files, DB
connections, temp directories you made yourself. `src/shop/db/uow.py`'s
`UnitOfWork.__aexit__` and this pattern solve the same problem in two different
places (a context manager for application code, a yield fixture for test setup).

## `request.addfinalizer` — the older, more flexible alternative

`yield` covers 95% of cases. `request.addfinalizer(callback)` exists for when you
need to register cleanup *conditionally*, or more than once, inside a fixture that
isn't itself written with `yield` (e.g. a factory fixture — see below — that creates
a variable number of things per test, each needing its own cleanup).

## `conftest.py` layering and overriding

A `conftest.py` fixture is visible to every test in its directory and below. A
`conftest.py` in a subdirectory can define a fixture with the *same name* as one
above it — the closer one wins for tests below it, and can even depend on the outer
one via the same fixture name as a parameter (pytest resolves this without infinite
recursion). See `examples/nested/conftest.py` overriding `examples/conftest.py`'s
`tax_rate` fixture, and `examples/nested/test_override.py` proving it.

## `request`: the fixture that describes the test asking for a fixture

`request` (built into pytest, always available) lets a fixture introspect the test
using it: `request.param` (module 02's indirect parametrization), `request.node`
(the test item itself — its name, its markers), and `request.addfinalizer`.

## `autouse=True`

A fixture applied to every applicable test automatically, without being named as a
parameter. Powerful and easy to overuse — an autouse fixture is invisible at the
call site, so a reader of the test has no clue it's running unless they already know
to check `conftest.py`. Reserve it for genuinely cross-cutting concerns (resetting
global state, seeding a deterministic random seed) — never for "convenient" test data
that a reader would expect to see explicitly requested.

## Factory-as-fixture

When a test needs *several, slightly different* instances of something (three
products with different stock levels), a plain fixture returning one object isn't
enough. The fix: a fixture that returns a *callable* — the callable is what actually
builds objects, with sensible defaults and overridable keyword arguments:

```python
@pytest.fixture
def make_product():
    created = []
    def _make(**overrides):
        product = Product(id=len(created), sku="SKU", name="Widget",
                           unit_price_cents=1000, stock_qty=10, **overrides)
        created.append(product)
        return product
    return _make
```

This is the pattern module 11's `polyfactory`-based factories generalize; understand
it by hand first. See `examples/test_factory_fixture.py`.

## `tmp_path`

A built-in fixture giving each test its own throwaway `pathlib.Path` directory,
auto-cleaned. Use it any time a test needs to touch the real filesystem (writing an
export file, reading a config file) without polluting the repo or other tests. See
`examples/test_tmp_path.py`.

## Exercise

```bash
make ex M=03
```

## You should now be able to

- Choose a fixture scope deliberately and explain the tradeoff.
- Write a `yield` fixture with teardown, and know when `request.addfinalizer` is the
  better tool instead.
- Override a fixture in a nested `conftest.py` and explain why the override wins.
- Write a factory-as-fixture for a domain object with overridable fields.
- Use `tmp_path` for a test that touches the filesystem.

## References

- pytest docs, "How to use fixtures" — https://docs.pytest.org/en/stable/how-to/fixtures.html
- pytest docs, "Fixture availability" (conftest.py scoping rules) —
  https://docs.pytest.org/en/stable/reference/fixtures.html#fixture-availability
- pytest docs, `tmp_path` — https://docs.pytest.org/en/stable/how-to/tmp_path.html
