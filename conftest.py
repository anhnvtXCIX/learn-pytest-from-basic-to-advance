"""Root conftest.py: repo-wide mechanics only. Teaching fixtures live in each
module's own `examples/conftest.py` (or, from module 13 onward, in `testkit/`) --
keep this file about pytest *plumbing*, not about the lesson content.
"""

from __future__ import annotations

import pathlib

import freezegun
import pytest

# On every freeze_time() start, freezegun getattr()s every attribute of every loaded
# module. testcontainers.core.config has a lazy module attribute that calls
# docker.from_env() -- with no Docker running that opens (and leaks) a unix socket to
# the daemon, surfacing as a random, flaky "unclosed socket" ResourceWarning-as-error
# in whichever test GC happens to run during. Keep freezegun out of it.
freezegun.configure(extend_ignore_list=["testcontainers"])

# Enables the `pytester` fixture (pytest's own "test pytest itself" plugin), used by
# modules/03-fixtures to prove fixture teardown timing without fighting test-order
# randomization in our own suite. Must be declared in the ROOT conftest.py -- pytest
# only looks for this at the rootdir.
pytest_plugins = ["pytester"]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-apply the `exercise` marker to every test collected from an `exercises/`
    or `solutions/` directory, so a fresh clone can run `pytest` and get a fully
    green suite without anyone having remembered to hand-mark 60-odd TODO/answer
    files. See `addopts` in pyproject.toml -- `exercise` tests are deselected there
    by default and opted back in with `make ex M=NN` / `make sol M=NN`.
    """
    exercise_dirs = {"exercises", "solutions"}
    for item in items:
        if exercise_dirs & set(pathlib.Path(str(item.fspath)).parts):
            item.add_marker(pytest.mark.exercise)
