# 04. Markers, config, and selection

## Custom markers and `--strict-markers`

`@pytest.mark.anything` works out of the box with no declaration — which is exactly
the problem: typo `@pytest.mark.slwo` and pytest silently accepts it as a new,
useless marker. This repo's `pyproject.toml` registers every marker it actually uses
under `[tool.pytest.ini_options] markers = [...]` and turns on `--strict-markers`,
which makes an *unregistered* marker a collection **error** instead of a silent
no-op. If you introduce a new marker, register it there first.

This repo's five markers: `unit`, `integration`, `docker`, `exercise`, `slow` — see
the root `pyproject.toml` for what each means and `Makefile` for how they're used to
select test tiers (`make test-unit`, `make test-docker`, etc).

## Selecting by marker: `-m`

```bash
uv run pytest -m unit                     # only unit-marked tests
uv run pytest -m "unit or integration"    # boolean expressions work
uv run pytest -m "not slow"               # exclude
```

**A gotcha worth knowing before it confuses you:** this repo's `addopts` already sets
`-m "not docker and not exercise"`. Passing your own `-m` on the command line does
**not** combine with that (it's not ANDed) — it *replaces* it entirely, because
`-m` is a single option value, and the command-line value wins over the one baked
into `addopts`. This is exactly why `Makefile`'s `ex` target runs
`pytest ... -m exercise` and gets exercise tests included, even though the default
config tries to exclude them: the explicit `-m exercise` on the command line
completely overrides `-m "not docker and not exercise"`, it doesn't get ANDed with
it (which would have selected nothing, since a test can't be both `exercise` and
`not exercise`). If you want to *add* a filter on top of the default instead of
replacing it, write out the whole expression yourself:
`pytest -m "not docker and not exercise and unit"`.

## `skip` and `skipif`

```python
@pytest.mark.skip(reason="not implemented yet")
def test_future_feature(): ...

@pytest.mark.skipif(sys.version_info < (3, 12), reason="needs 3.12+ typing syntax")
def test_new_syntax(): ...
```

Use `skip`/`skipif` for "this test cannot meaningfully run right now" (missing
dependency, wrong platform, not-yet-built feature) — not as a way to silence a test
that's failing for a real reason. A growing pile of skipped tests is a maintenance
debt exactly like a growing pile of `# TODO` comments; periodically ask whether each
skip condition is still true.

## `xfail`: expected to fail, and the difference `strict` makes

```python
@pytest.mark.xfail(reason="known bug, see TICKET-123")
def test_known_bug(): ...
```

Three possible outcomes, and this is the part worth understanding precisely:

- The test fails → reported as **XFAIL** (expected failure). Counts as a "pass" for
  CI purposes either way.
- The test passes, `strict=False` (the default) → reported as **XPASS**. Still
  doesn't fail the run — a soft "huh, that's interesting" signal only visible if you
  look for it (`-rxX` shows both XFAIL and XPASS lines explicitly).
- The test passes, `strict=True` → reported as a **hard FAILURE**. This is what you
  want for "I expect this to be broken until PR #456 lands" — the moment it starts
  passing, `strict=True` forces you to notice and remove the marker, instead of the
  fix silently going unnoticed under an `xfail` nobody revisits.

`examples/test_xfail_strict.py` proves this distinction using `pytester` (module 03's
technique) rather than asserting it in prose, since we can't leave a permanently
strict-xfail-that-unexpectedly-passes lying around in our own suite without breaking
`make test`.

**Default to `strict=True`** for any `xfail` you write. `strict=False` is the right
choice only when a test is genuinely flaky in a way you haven't fixed yet (sometimes
fails, sometimes doesn't) — and even then, treat it as a debt to pay down, not a
permanent home.

## `filterwarnings`, per-test

The ini-level `filterwarnings = ["error"]` (root `pyproject.toml`) means *any*
warning fails *any* test by default — a deliberately strict default that catches
deprecations early. For the rare legitimate exception, mark the specific test:

```python
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_the_one_place_we_still_call_the_deprecated_thing(): ...
```

Prefer narrowing to the specific warning class (and ideally the specific module, as
the root config does for httpx) over broadly silencing everything in a test — a
blanket ignore can hide a second, unrelated, real warning.

## Exercise

```bash
make ex M=04
```

## You should now be able to

- Explain why this repo enables `--strict-markers`, and register a new marker
  correctly if you introduce one.
- Predict what `-m "unit"` does when `addopts` already has its own `-m` clause.
- Choose between `skip`, `skipif`, and `xfail` for a given situation, and explain
  what `xfail(strict=True)` buys you over the default.

## References

- pytest docs, "Marking test functions with attributes" —
  https://docs.pytest.org/en/stable/how-to/mark.html
- pytest docs, "Skip and xfail: dealing with tests that cannot succeed" —
  https://docs.pytest.org/en/stable/how-to/skipping.html
- pytest docs, "How to capture warnings" —
  https://docs.pytest.org/en/stable/how-to/capture-warnings.html
