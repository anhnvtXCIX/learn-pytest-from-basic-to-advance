# 00. Getting started

## Setup

```bash
make install   # uv sync + alembic upgrade head
make test      # confirm you're green before changing anything
```

## How pytest finds your tests

Rules (from `pyproject.toml`'s `testpaths = ["modules", "src"]` plus pytest's
defaults):

- Files matching `test_*.py` or `*_test.py`.
- Inside them, functions named `test_*` and classes named `Test*` (classes must have
  no `__init__`) with methods named `test_*`.
- `conftest.py` files are special: never imported directly, auto-discovered by
  pytest for fixtures, and scoped to their directory and everything below it. A
  `conftest.py` in `modules/00-getting-started/examples/` only applies to tests in
  that folder; the root `conftest.py` applies everywhere.

Run `uv run pytest --collect-only -q` from the repo root right now and read the
output — that list *is* what "discovery" means, made concrete.

## Command-line flags worth knowing on day one

Try each of these from the repo root against `modules/00-getting-started/examples/`:

```bash
uv run pytest modules/00-getting-started/examples -v          # verbose: one line per test
uv run pytest modules/00-getting-started/examples -k discount # only tests whose name matches "discount"
uv run pytest modules/00-getting-started/examples -m slow      # only tests marked @pytest.mark.slow
uv run pytest modules/00-getting-started/examples -x           # stop after the first failure
uv run pytest modules/00-getting-started/examples --lf         # rerun only Last Failed
uv run pytest modules/00-getting-started/examples --sw         # stepwise: like --lf but stops again at the same test
uv run pytest modules/00-getting-started/examples -vv          # extra-verbose: full assertion diffs
uv run pytest modules/00-getting-started/examples --durations=5 # slowest 5 tests, always worth checking periodically
```

`-k EXPR` matches against test (and file/class) names using a small Python-like
expression language: `-k "discount and not tier3"` works.

## Assertion introspection

pytest rewrites plain `assert` statements at import time to show you *why* they
failed — no `self.assertEqual` ceremony needed. `assert totals.total_cents == 3300`
on failure shows both sides' actual values, and for collections/dicts, a diff. This
only works for `assert`, not e.g. `if not x: raise AssertionError()` — always prefer
a bare `assert`.

## Random test order (`pytest-randomly`)

This repo runs with `pytest-randomly` (see `pyproject.toml`'s dev dependencies)
which shuffles test order every run by default, and prints the seed it used:
`Using --randomly-seed=1234`. This is deliberate — see
`docs/04-coverage-and-quality.md`'s section on flakiness: a suite that only passes in
one specific order has a real, hidden bug (shared state between tests), and finding
that out on day one is much better than finding it out in CI six months from now. To
reproduce a specific run's order (e.g. to debug a failure), pass that seed back:
`uv run pytest -p randomly --randomly-seed=1234`. To turn shuffling off entirely for
one run: `uv run pytest -p no:randomly`.

## Exercise

Open `exercises/test_pricing_basics.py` and make the TODO tests pass. Then:

```bash
make ex M=00
```

Compare your answer against `solutions/test_pricing_basics.py` once it's green —
don't peek first.

## You should now be able to

- Explain what `testpaths`, `conftest.py`, and marker-based `addopts` filtering do in
  this repo's `pyproject.toml`.
- Use `-k`, `-m`, `-x`, `--lf`, `--durations` without looking them up.
- Explain why this repo runs with randomized test order by default.

## References

- pytest docs, "How to invoke pytest" — <https://docs.pytest.org/en/stable/how-to/usage.html>
- pytest docs, "Good Integration Practices" (discovery rules) —
  <https://docs.pytest.org/en/stable/explanation/goodpractices.html>
