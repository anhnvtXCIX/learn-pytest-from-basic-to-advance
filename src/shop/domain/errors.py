"""Domain-level exceptions.

These are raised by `services/orders.py` and translated to HTTP responses in
`api/routes.py`. Keeping them separate from SQLAlchemy's or httpx's exceptions is what
lets the service layer stay ignorant of *how* stock or payment are implemented --
which is exactly what makes it possible to test the service with fakes (module 05).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all expected, "business" errors."""


class ProductNotFoundError(DomainError):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"product {product_id} not found")
        self.product_id = product_id


class InvalidOrderError(DomainError):
    """Raised for structurally invalid orders (e.g. zero lines, zero quantity)."""


class InsufficientStockError(DomainError):
    def __init__(self, product_id: int, requested: int, available: int) -> None:
        super().__init__(
            f"product {product_id}: requested {requested}, only {available} in stock"
        )
        self.product_id = product_id
        self.requested = requested
        self.available = available


class PaymentDeclinedError(DomainError):
    """The gateway made a business decision to refuse the charge. Not retryable
    without changing something (a different card, a smaller amount, ...).
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"payment declined: {reason}")
        self.reason = reason


class PaymentGatewayUnavailableError(DomainError):
    """The gateway call itself failed (timeout, 5xx, connection error). Retryable --
    this is deliberately a different exception than `PaymentDeclinedError` so callers
    (and tests) can tell "no" from "couldn't ask" apart. See module 08.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"payment gateway unavailable: {reason}")
        self.reason = reason


class DuplicateOrderError(DomainError):
    """Raised when an idempotency key has already been used for a different order."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(f"idempotency key {idempotency_key!r} already used")
        self.idempotency_key = idempotency_key


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: int) -> None:
        super().__init__(f"order {order_id} not found")
        self.order_id = order_id


class InvalidOrderStateError(DomainError):
    """Raised when an operation (e.g. cancel) isn't valid for the order's current status."""
