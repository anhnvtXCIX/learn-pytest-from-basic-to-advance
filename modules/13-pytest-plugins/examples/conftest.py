"""`pytest_collection_modifyitems` and hook ordering, scoped to this directory only
(unlike testkit/plugin.py's fixtures, which are repo-wide -- collection-changing
hooks are risky to apply globally this late with 12 other modules already relying on
today's collection order, so this one stays local, on purpose).

Multiple plugins (this repo has several: pytest-randomly, this conftest.py, the root
conftest.py) can each implement `pytest_collection_modifyitems`, and pytest calls
ALL of them. Which one runs first/last is controlled by `@pytest.hookimpl(tryfirst=True
/ trylast=True)` plus plugin registration order and internals that can change
between pytest versions. Empirically, in this repo today, this hook's `items.sort()`
already lands after pytest-randomly's shuffle even without `trylast=True` -- checked
directly by temporarily removing it and re-running the ordering check in
test_hook_ordering.py's docstring several times. `trylast=True` is kept anyway,
specifically BECAUSE that ordering isn't something this file's code controls or
should rely on implicitly: it's a real pytest option that says outright "I want this
to run after other implementations of this hook," which is what's actually meant
here, rather than leaning on default behavior that happens to agree today.
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    items.sort(key=lambda item: item.name.startswith("test_z_"))
