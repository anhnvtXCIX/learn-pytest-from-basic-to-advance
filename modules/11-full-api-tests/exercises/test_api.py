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
    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "exercise-key-1",
        },
    )

    assert response.status_code == 201
    body = response.json()
    print()
    assert "id" in body
    assert "customer_ref" in body
    assert "status" in body
    assert "lines" in body
    assert "subtotal_cents" in body
    assert "discount_cents" in body
    assert "tax_cents" in body
    assert "total_cents" in body
    assert "payment_reference" in body
    assert "created_at" in body


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
    # First try
    response_1 = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "exercise-key",
        },
    )

    # Create order the second time
    response_2 = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 3}],
            "idempotency_key": "exercise-key",
        },
    )

    assert response_1.status_code == response_2.status_code == 201

    order_1, order_2 = response_1.json(), response_2.json()
    assert order_1["id"] == order_2["id"]
    assert order_1["total_cents"] == order_2["total_cents"]


async def test_cancelling_an_already_refunded_order_is_409(
    client, auth_headers, seeded_product: Product
) -> None:
    """TODO: create an order, cancel it once (should succeed, 200), then cancel the
    SAME order_id a second time and assert the second cancel returns 409 (an
    already-refunded order isn't a valid target for cancel_order -- see
    InvalidOrderStateError in services/orders.py).
    """
    repsonse_1 = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "exercise-key",
        },
    )

    order_id = repsonse_1.json()["id"]

    # Cancel the order first time
    resp_cancel_1 = await client.post(
        f"/orders/{order_id}/cancel",
        headers=auth_headers,
    )

    assert resp_cancel_1.status_code == 200

    # Second attempt to cancel the order
    resp_cancel_1 = await client.post(
        f"/orders/{order_id}/cancel",
        headers=auth_headers,
    )

    assert resp_cancel_1.status_code == 409
