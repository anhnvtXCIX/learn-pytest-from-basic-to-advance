"""FastAPI dependencies.

`get_order_service` is the seam module 07/11 exercise most: tests replace it wholesale
with `app.dependency_overrides[get_order_service] = lambda: fake_service` to test the
API layer (routing, status codes, JSON shape) without touching a database at all, or
leave it alone and get the real thing for full-stack tests.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from shop.config import Settings
from shop.services.orders import OrderService


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_order_service(request: Request) -> OrderService:
    service: OrderService = request.app.state.order_service
    return service


async def require_api_key(
    request: Request, x_api_key: str | None = Header(default=None)
) -> None:
    settings = get_settings(request)
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
