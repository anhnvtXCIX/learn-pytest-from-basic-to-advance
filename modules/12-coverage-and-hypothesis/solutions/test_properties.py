"""Reference solution for exercises/test_properties.py."""

from __future__ import annotations

from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_subtotal_cents

order_lines_strategy = st.lists(
    st.builds(
        OrderLine,
        product_id=st.integers(min_value=1, max_value=1_000),
        quantity=st.integers(min_value=1, max_value=100),
        unit_price_cents=st.integers(min_value=0, max_value=1_000_000),
    ),
    min_size=1,
    max_size=10,
)


@given(order_lines_strategy)
def test_subtotal_is_never_negative(lines: list[OrderLine]) -> None:
    assert calculate_subtotal_cents(lines) >= 0


@given(order_lines_strategy)
def test_subtotal_scales_with_a_uniform_price_increase(lines: list[OrderLine]) -> None:
    raised_lines = [replace(line, unit_price_cents=line.unit_price_cents + 100) for line in lines]
    total_quantity = sum(line.quantity for line in lines)

    assert calculate_subtotal_cents(raised_lines) == calculate_subtotal_cents(lines) + (
        100 * total_quantity
    )


class CounterModel:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        self.value += 1

    def decrement(self) -> None:
        self.value -= 1


class CounterMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.model = CounterModel()

    @rule()
    def increment(self) -> None:
        self.model.increment()

    @rule()
    def decrement(self) -> None:
        if self.model.value > 0:
            self.model.decrement()

    @invariant()
    def value_never_negative(self) -> None:
        assert self.model.value >= 0


TestCounterMachine = CounterMachine.TestCase
