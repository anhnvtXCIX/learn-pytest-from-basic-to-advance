"""Exercise: Hypothesis properties and stateful testing.

    make ex M=12
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from shop.domain.models import OrderLine

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
    # TODO: assert calculate_subtotal_cents(lines) >= 0 -- a one-line property, but
    # notice Hypothesis still generates dozens of varied cases to check it against.
    raise NotImplementedError("write this test")


@given(order_lines_strategy)
def test_subtotal_scales_with_a_uniform_price_increase(lines: list[OrderLine]) -> None:
    """TODO: build a second list of lines identical to `lines` but with every line's
    unit_price_cents increased by 100. Assert the new subtotal equals the original
    subtotal PLUS (100 * total quantity across all lines). This is a stronger,
    more specific property than "isn't negative" -- it pins down the actual
    relationship, not just a sanity bound.
    """
    raise NotImplementedError("write this test")


class CounterModel:
    """A trivial up/down counter with a floor at zero -- TODO: model it below."""

    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        self.value += 1

    def decrement(self) -> None:
        # TODO (in the state machine below, not here): decrement should never be
        # called when value == 0 in a way that would make it negative -- the state
        # machine's rule should guard against that, the same way StockMachine's
        # `release` rule guards against releasing more than was reserved.
        self.value -= 1


class CounterMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.model = CounterModel()

    @rule()
    def increment(self) -> None:
        # TODO: call self.model.increment()
        raise NotImplementedError("implement this rule")

    @rule()
    def decrement(self) -> None:
        # TODO: only call self.model.decrement() if self.model.value > 0 -- guard
        # the same way StockMachine's `release` rule guards its precondition.
        raise NotImplementedError("implement this rule")

    @invariant()
    def value_never_negative(self) -> None:
        # TODO: assert self.model.value >= 0
        raise NotImplementedError("implement this invariant")


TestCounterMachine = CounterMachine.TestCase
