"""Every distinct error path routes.py maps -- each is its own test with its own
status-code assertion, per docs/03-what-to-test.md's "test error paths deliberately."
"""

from __future__ import annotations

import pytest

from shop.db.uow import UnitOfWork
from shop.domain.models import Product


async def test_missing_api_key_is_rejected(client) -> None:
    response = await client.get("/orders/1")

    assert response.status_code == 401


async def test_wrong_api_key_is_rejected(client) -> None:
    response = await client.get("/orders/1", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401


async def test_get_nonexistent_order_is_404(client, auth_headers) -> None:
    response = await client.get("/orders/999999", headers=auth_headers)

    assert response.status_code == 404


async def test_create_order_for_nonexistent_product_is_422(client, auth_headers) -> None:
    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": 999999, "quantity": 1}],
            "idempotency_key": "error-key-1",
        },
    )

    assert response.status_code == 422


async def test_create_order_with_insufficient_stock_is_409(
    client, auth_headers, seeded_product: Product
) -> None:
    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 999}],
            "idempotency_key": "error-key-2",
        },
    )

    assert response.status_code == 409


async def test_create_order_declined_by_payment_gateway_is_402(
    client, auth_headers, sessionmaker
) -> None:
    """A dedicated, expensive product for this test -- `seeded_product` (module
    conftest.py) is priced too low to ever cross the fake gateway's $1,000 decline
    threshold, however much of it you order (its stock_qty caps that). This is
    itself worth noticing: the first version of this test used `seeded_product`
    with a large `quantity` and got a false-positive-looking 201, silently testing
    nothing about the decline path at all until the assertion caught it.
    """
    async with UnitOfWork(sessionmaker) as uow:
        expensive = await uow.products.add(
            Product(id=0, sku="EXPENSIVE", name="Expensive", unit_price_cents=50_000, stock_qty=5)
        )
        await uow.commit()

    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": expensive.id, "quantity": 3}],  # 150,000 cents
            "idempotency_key": "error-key-3",
        },
    )

    assert response.status_code == 402


async def test_create_order_with_zero_quantity_is_a_validation_error(
    client, auth_headers, seeded_product: Product
) -> None:
    """Caught by the pydantic schema itself (RequestedLineIn.quantity: gt=0) -- never
    reaches OrderService at all, so this is a 422 for a different reason than the
    "product not found" 422 above (FastAPI's own request-validation error shape).
    """
    response = await client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_ref": "cust-1",
            "lines": [{"product_id": seeded_product.id, "quantity": 0}],
            "idempotency_key": "error-key-4",
        },
    )

    assert response.status_code == 422


@pytest.mark.skip(
    reason="cancel_order only accepts a PAID order (services/orders.py), but this "
    "fixture setup's fake gateway always succeeds for small amounts, so there's no "
    "easy way to get an order stuck in PENDING through the API as it stands -- see "
    "modules/05-test-double-taxonomy/exercises for this exact path tested directly "
    "against OrderService instead, where it's a two-line fixture change."
)
async def test_cancel_a_pending_order_is_409() -> None:
    raise NotImplementedError
