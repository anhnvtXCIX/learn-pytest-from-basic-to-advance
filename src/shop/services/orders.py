"""`OrderService`: the orchestration layer, and the main character of this repo.

This is where "integration testing" and "mocking" stop being abstract ideas and start
being a concrete design question: which of this method's four collaborators (a unit
of work, a payment gateway, an idempotency lock, a clock) should a given test replace
with a double, and which should be real?

- modules/05-08 test this class with every collaborator faked, to pin down its
  *orchestration logic* (call order, error handling, compensation) in isolation.
- modules/09-11 test it with a real database and a real (Testcontainers) Redis, but
  still a fake payment gateway -- because "real" for an owned database means
  something different than "real" for a third party's payment API. See
  docs/05-backend-testing-playbook.md for the general version of this rule.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from shop.clock import Clock
from shop.db.uow import SupportsUnitOfWork
from shop.domain.errors import (
    DuplicateOrderError,
    InvalidOrderStateError,
    OrderNotFoundError,
    PaymentDeclinedError,
    PaymentGatewayUnavailableError,
    ProductNotFoundError,
)
from shop.domain.models import Order, OrderLine, OrderStatus, RequestedLine
from shop.domain.pricing import calculate_totals
from shop.gateways.cache import IdempotencyLock
from shop.gateways.payments import PaymentGateway

_LOCK_TTL_SECONDS = 30


class OrderService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], SupportsUnitOfWork],
        payment_gateway: PaymentGateway,
        idempotency_lock: IdempotencyLock,
        clock: Clock,
        tax_rate: float,
    ) -> None:
        self._uow_factory = uow_factory
        self._payment_gateway = payment_gateway
        self._lock = idempotency_lock
        self._clock = clock
        self._tax_rate = tax_rate

    async def place_order(
        self,
        *,
        customer_ref: str,
        requested_lines: Sequence[RequestedLine],
        idempotency_key: str,
    ) -> Order:
        # 1. Idempotent replay: if we've already fully processed this key, hand back
        #    the same order rather than doing any work (this check needs no lock --
        #    it's only a *concurrent* duplicate that the lock below protects against).
        async with self._uow_factory() as uow:
            existing = await uow.orders.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        # 2. Guard against a *concurrent* duplicate: two requests carrying the same
        #    key, arriving close enough together that neither has committed an order
        #    yet. Whoever loses this race fails fast instead of double-charging.
        if not await self._lock.acquire(idempotency_key, ttl_seconds=_LOCK_TTL_SECONDS):
            raise DuplicateOrderError(idempotency_key)

        try:
            async with self._uow_factory() as uow:
                # Resolve prices ourselves and reserve stock in the same transaction
                # -- never trust a client-supplied price, and never let "check stock"
                # and "commit to selling it" be two separate, racy steps.
                order_lines: list[OrderLine] = []
                for requested in requested_lines:
                    product = await uow.products.get(requested.product_id)
                    if product is None:
                        raise ProductNotFoundError(requested.product_id)
                    await uow.products.reserve_stock(requested.product_id, requested.quantity)
                    order_lines.append(
                        OrderLine(
                            product_id=requested.product_id,
                            quantity=requested.quantity,
                            unit_price_cents=product.unit_price_cents,
                        )
                    )

                totals = calculate_totals(order_lines, self._tax_rate)
                order = Order(
                    id=None,
                    customer_ref=customer_ref,
                    status=OrderStatus.PENDING,
                    lines=order_lines,
                    totals=totals,
                    idempotency_key=idempotency_key,
                    created_at=self._clock.now(),
                )
                order = await uow.orders.add(order)
                await uow.commit()
                assert order.id is not None  # add() always assigns one; documents that for mypy

            try:
                payment_reference = await self._payment_gateway.charge(
                    amount_cents=totals.total_cents,
                    currency="usd",
                    reference=idempotency_key,
                )
            except (PaymentDeclinedError, PaymentGatewayUnavailableError):
                await self._release_reservation(order)
                raise

            async with self._uow_factory() as uow:
                await uow.orders.mark_paid(order.id, payment_reference=payment_reference)
                await uow.commit()

            order.status = OrderStatus.PAID
            order.payment_reference = payment_reference
            return order
        finally:
            await self._lock.release(idempotency_key)

    async def _release_reservation(self, order: Order) -> None:
        """Compensating action when payment fails after stock was already reserved."""
        assert order.id is not None  # always called with an order that's already been add()ed
        async with self._uow_factory() as uow:
            for line in order.lines:
                await uow.products.release_stock(line.product_id, line.quantity)
            await uow.orders.mark_cancelled(order.id)
            await uow.commit()

    async def get_order(self, order_id: int) -> Order:
        async with self._uow_factory() as uow:
            order = await uow.orders.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def cancel_order(self, order_id: int) -> Order:
        async with self._uow_factory() as uow:
            order = await uow.orders.get(order_id)
            if order is None:
                raise OrderNotFoundError(order_id)
            if order.status != OrderStatus.PAID:
                raise InvalidOrderStateError(
                    f"order {order_id} has status {order.status}, "
                    "only a paid order can be cancelled"
                )

            if order.payment_reference is not None:
                # Deliberately not caught: if the refund call fails, we want this
                # whole method to raise and the `async with` above to roll back the
                # stock release and status change along with it. A partially-refunded
                # order (money back, stock not restored) is worse than a clean retry.
                await self._payment_gateway.refund(
                    payment_reference=order.payment_reference,
                    amount_cents=order.totals.total_cents,
                )

            for line in order.lines:
                await uow.products.release_stock(line.product_id, line.quantity)
            await uow.orders.mark_refunded(order_id)
            await uow.commit()

        order.status = OrderStatus.REFUNDED
        return order
