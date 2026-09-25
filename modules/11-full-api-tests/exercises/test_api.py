"""Exercise: full-stack API tests.

    make ex M=11
"""

from __future__ import annotations

from shop.domain.models import Product


async def test_create_order_returns_the_right_json_shape(
    client, auth_headers, seeded_product: Product
) -> None:
    """TODO: POST a valid order for `seeded_product` (quantity=1), assert
    status_code == 201, and assert the response body has all of: "id",
    "customer_ref", "status", "lines", "subtotal_cents", "discount_cents",
    "tax_cents", "total_cents", "payment_reference", "created_at" -- i.e. that the
    full OrderOut contract (src/shop/api/schemas.py) is actually present, not just
    the couple of fields other tests happen to check.
    """
    raise NotImplementedError("write this test")


async def test_replaying_the_same_idempotency_key_ignores_a_different_payload(
    client, auth_headers, seeded_product: Product
) -> None:
    """TODO: POST an order for quantity=1 with idempotency_key="exercise-key".
    Then POST AGAIN with the SAME idempotency_key but quantity=3 this time. Assert
    both responses are 201 with the SAME order id, and that the second response's
    total_cents matches the FIRST request's total (quantity=1's price), not a
    quantity=3 price -- proving the replay short-circuits before re-pricing anything,
    exactly as services/orders.py's `place_order` comment says it should.
    """
    raise NotImplementedError("write this test")


async def test_cancelling_an_already_refunded_order_is_409(
    client, auth_headers, seeded_product: Product
) -> None:
    """TODO: create an order, cancel it once (should succeed, 200), then cancel the
    SAME order_id a second time and assert the second cancel returns 409 (an
    already-refunded order isn't a valid target for cancel_order -- see
    InvalidOrderStateError in services/orders.py).
    """
    raise NotImplementedError("write this test")
