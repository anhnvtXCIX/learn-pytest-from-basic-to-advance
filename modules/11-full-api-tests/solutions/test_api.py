"""Reference solution for exercises/test_api.py."""

from __future__ import annotations

from shop.domain.models import Product


async def test_create_order_returns_the_right_json_shape(
    client, auth_headers, seeded_product: Product
) -> None:
    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "shape-key",
        },
    )

    assert response.status_code == 201
    body = response.json()
    expected_fields = {
        "id",
        "customer_ref",
        "status",
        "lines",
        "subtotal_cents",
        "discount_cents",
        "tax_cents",
        "total_cents",
        "payment_reference",
        "created_at",
    }
    assert expected_fields <= body.keys()


async def test_replaying_the_same_idempotency_key_ignores_a_different_payload(
    client, auth_headers, seeded_product: Product
) -> None:
    first = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "exercise-key",
        },
    )
    second = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 3}],
            "idempotency_key": "exercise-key",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["total_cents"] == first.json()["total_cents"]


async def test_cancelling_an_already_refunded_order_is_409(
    client, auth_headers, seeded_product: Product
) -> None:
    create_response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 1}],
            "idempotency_key": "double-cancel-key",
        },
    )
    order_id = create_response.json()["id"]

    first_cancel = await client.post(f"/orders/{order_id}/cancel", headers=auth_headers)
    second_cancel = await client.post(f"/orders/{order_id}/cancel", headers=auth_headers)

    assert first_cancel.status_code == 200
    assert second_cancel.status_code == 409
