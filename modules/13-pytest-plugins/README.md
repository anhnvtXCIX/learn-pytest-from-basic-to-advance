# 13. Extending pytest: writing your own plugin

Modules 05 through 11 each built (or copied) the same handful of fakes and
factories into their own local `conftest.py`, on purpose (see CLAUDE.md) — the
duplication was the point, until now. This module is where you'd normally *notice*
that duplication and extract it. It's already been extracted for you, into
`testkit/`, at the repo root: read that refactor, then use the two lower-level hooks
(`pytest_addoption`, `pytest_collection_modifyitems`) it's built on.

## From `conftest.py` fixtures to an installable plugin

A `conftest.py` file's fixtures are visible to its directory and below (module 03).
A **pytest plugin** is the same fixture mechanism, packaged so it's visible
*everywhere*, the moment the package that ships it is installed — no import, no
`conftest.py` needed at the call site. The entire difference is three things:

1. The fixtures live in an ordinary Python module (`testkit/plugin.py`), not a file
   pytest auto-discovers by name.
2. That module is registered under the `pytest11` entry point group in
   `pyproject.toml`:
   ```toml
   [project.entry-points.pytest11]
   testkit = "testkit.plugin"
   ```
3. The package is installed (`uv sync`, which reinstalls this project editable
   every time — see `pyproject.toml`'s `[tool.hatch.build.targets.wheel]` comment).

`examples/test_plugin_fixtures.py` has **no local `conftest.py`** and uses
`fake_clock`, `fake_uow`, `fake_lock`, `fake_gateway`, and `product_factory` anyway —
compare it directly against
`modules/05-test-double-taxonomy/examples/conftest.py`, which built the same fakes
by hand, locally, the first time this repo needed them.

A fixture with the same name defined in a *local* `conftest.py` still wins over the
plugin's version for tests under that directory — same "closer wins" rule as module
03's nested `conftest.py` example, just with the plugin now playing the role of the
outermost, repo-wide layer.

## `pytest_addoption`: your own CLI flags

`testkit/plugin.py` adds `--fake-now`, consumed by the `fake_clock` fixture via
`request.config.getoption(...)`:

```bash
uv run pytest modules/13-pytest-plugins/examples --fake-now=2030-06-15 -v
```

`examples/test_plugin_fixtures.py::test_fake_clock_uses_the_cli_option` asserts on
whatever value was actually passed — real proof the option reaches the fixture, not
just a description of the mechanism.

## `pytest_collection_modifyitems` and hook ordering

`examples/conftest.py` implements this hook to force any `test_z_*`-named test to
run last, regardless of pytest-randomly's shuffle — verified directly (not assumed)
by running `--collect-only` several times and checking the position. Multiple
plugins can implement the *same* hook name; pytest calls all of them, and
`@pytest.hookimpl(tryfirst=True)` / `trylast=True` state your intent about relative
ordering explicitly, which matters because the *default* ordering depends on
registration order and internals that can shift between pytest versions — see that
file's docstring for what was actually checked while writing it (including a case
where removing `trylast=True` made no visible difference *today*, which is exactly
why declaring intent explicitly still beats relying on that).

This hook is deliberately kept in a **local** `conftest.py`, not the global
`testkit` plugin — reordering collected tests repo-wide, this late, with twelve
other modules already relying on today's collection behavior, is a bigger blast
radius than this module's lesson needs. Real judgement call, stated outright: not
everything that *can* go in a shared plugin *should*.

## Exercise

```bash
make ex M=13
```

## You should now be able to

- Explain the three things that turn a `conftest.py` fixture into a plugin fixture.
- Add a custom CLI option with `pytest_addoption` and consume it in a fixture.
- Write a `pytest_collection_modifyitems` hook and reason about its ordering
  relative to other plugins.
- Explain why this repo scoped the collection hook locally but the fixtures
  globally, as a real example of judging blast radius rather than a fixed rule.

## References

- pytest docs, "Writing plugins" — https://docs.pytest.org/en/stable/how-to/writing_plugins.html
- pytest docs, hook function ordering / `hookwrapper` —
  https://docs.pytest.org/en/stable/how-to/writing_hook_functions.html
- pluggy docs (the hook-calling library pytest is built on) — https://pluggy.readthedocs.io/
