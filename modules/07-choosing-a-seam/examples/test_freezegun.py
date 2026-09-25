"""Why time gets a dedicated library, and the two ways this repo actually controls it."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from freezegun import freeze_time

from shop.clock import Clock, SystemClock


def test_datetime_cannot_be_monkeypatched_directly() -> None:
    """Proof, not assertion-by-assertion prose: datetime.datetime is a C-implemented
    immutable type. This is the actual reason freezegun exists.
    """
    with pytest.raises(TypeError, match="immutable type"):
        datetime.now = lambda: "patched"  # type: ignore[method-assign]


def test_freezegun_controls_the_real_stdlib_call() -> None:
    """freezegun reaches code that calls datetime.now() directly -- including
    SystemClock, which does exactly that (src/shop/clock.py) and has no idea
    freezegun exists.
    """
    with freeze_time("2030-06-15 08:00:00"):
        assert SystemClock().now() == datetime(2030, 6, 15, 8, 0, 0, tzinfo=UTC)


def test_freezegun_time_passing() -> None:
    """freeze_time also supports advancing the frozen clock explicitly, for testing
    time-dependent sequences (e.g. "the lock expired after 30 seconds").
    """
    with freeze_time("2030-01-01 00:00:00") as frozen:
        start = SystemClock().now()
        frozen.tick(delta=30)
        later = SystemClock().now()

    assert (later - start).total_seconds() == 30


class UsesInjectedClock:
    """The preferred style for code you're writing: accept a Clock, don't reach for
    datetime.now() at all. Contrast with SystemClock above, which freezegun has to
    intercept because there's no seam to inject into.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def timestamp_label(self) -> str:
        return self._clock.now().isoformat()


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def test_dependency_injection_needs_no_special_library() -> None:
    thing = UsesInjectedClock(FixedClock(datetime(2030, 1, 1, tzinfo=UTC)))

    assert thing.timestamp_label() == "2030-01-01T00:00:00+00:00"
