"""HTTP routes. Thin on purpose: each handler's job is to translate between the HTTP
contract (schemas.py) and `OrderService`, and to translate domain exceptions into HTTP
status codes. No business logic lives here -- that's what makes `OrderService`
testable without an HTTP layer at all (modules 05-10), and this file testable with
every domain exception it might see (module 11).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from shop.api.deps import get_order_service, require_api_key
from shop.api.schemas import CreateOrderRequest, OrderOut
from shop.domain.errors import (
    DuplicateOrderError,
    InsufficientStockError,
    InvalidOrderError,
    InvalidOrderStateError,
    OrderNotFoundError,
    PaymentDeclinedError,
    PaymentGatewayUnavailableError,
    ProductNotFoundError,
)
from shop.domain.models import RequestedLine
from shop.services.orders import OrderService

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    try:
        order = await service.place_order(
            customer_ref=payload.customer_ref,
            requested_lines=[
                RequestedLine(product_id=line.product_id, quantity=line.quantity)
                for line in payload.lines
            ],
            idempotency_key=payload.idempotency_key,
        )
    except (ProductNotFoundError, InvalidOrderError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except DuplicateOrderError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except PaymentDeclinedError as exc:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc)) from exc
    except PaymentGatewayUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return OrderOut.from_domain(order)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    try:
        order = await service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return OrderOut.from_domain(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    try:
        order = await service.cancel_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidOrderStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except PaymentGatewayUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return OrderOut.from_domain(order)
