"""Stateful testing: instead of one input in, one output out, Hypothesis generates a
random SEQUENCE of operations and checks an invariant holds after every single one.

This models the same reserve/release logic as
`ProductRepository.reserve_stock`/`release_stock` (src/shop/db/repository.py), kept
synchronous and dependency-free here so the stateful-testing technique itself is the
focus, not async plumbing -- the invariants being checked (never negative, always
conserved) are exactly the ones that matter for the real thing too.
"""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

INITIAL_STOCK = 20


class StockModel:
    """A synchronous stand-in for the stock-reservation logic that lives in
    `ProductRepository.reserve_stock`/`release_stock`.
    """

    def __init__(self, initial_stock: int) -> None:
        self.stock_qty = initial_stock

    def reserve(self, quantity: int) -> bool:
        if self.stock_qty < quantity:
            return False
        self.stock_qty -= quantity
        return True

    def release(self, quantity: int) -> None:
        self.stock_qty += quantity


class StockMachine(RuleBasedStateMachine):
    """Hypothesis calls `reserve`/`release` in random order, with random quantities,
    any number of times, and checks BOTH `@invariant`s after every single call --
    not just at the end. A bug that only manifests after a specific 7-step sequence
    of reserves and releases is exactly what this technique finds and a hand-picked
    unit test almost certainly wouldn't.
    """

    def __init__(self) -> None:
        super().__init__()
        self.model = StockModel(initial_stock=INITIAL_STOCK)
        self.reserved_total = 0

    @rule(quantity=st.integers(min_value=1, max_value=10))
    def reserve(self, quantity: int) -> None:
        if self.model.reserve(quantity):
            self.reserved_total += quantity

    @rule(quantity=st.integers(min_value=1, max_value=10))
    def release(self, quantity: int) -> None:
        # Only release up to what's actually outstanding -- releasing more than was
        # ever reserved isn't a scenario the real repository allows either (nothing
        # calls release_stock for a reservation it doesn't hold).
        if quantity <= self.reserved_total:
            self.model.release(quantity)
            self.reserved_total -= quantity

    @invariant()
    def stock_never_goes_negative(self) -> None:
        assert self.model.stock_qty >= 0

    @invariant()
    def stock_is_always_conserved(self) -> None:
        """Nothing is ever created or destroyed: available + reserved always equals
        what we started with, no matter what sequence of operations got us here.
        """
        assert self.model.stock_qty + self.reserved_total == INITIAL_STOCK


TestStockMachine = StockMachine.TestCase
