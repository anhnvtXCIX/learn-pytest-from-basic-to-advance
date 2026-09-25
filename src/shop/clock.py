"""A `Clock` seam.

Code that calls `datetime.now()` (or `utcnow()`) directly is hard to test: you can't
assert on a value you don't control, and you can't easily test "what happens right at
midnight" or "what happens if two calls a microsecond apart get the same timestamp".

The fix is to make time an injected dependency, just like a database session or an
HTTP client. Production code gets a `SystemClock`; tests get a fixed, fake clock (see
modules/07-choosing-a-seam) or `freezegun` (also module 07).

Reference: Fowler, "Eradicating Non-Determinism in Tests" --
https://martinfowler.com/articles/nonDeterminism.html
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Anything that can tell you the current UTC time."""

    def now(self) -> datetime: ...


class SystemClock:
    """The real clock. Used everywhere except tests."""

    def now(self) -> datetime:
        return datetime.now(UTC)
