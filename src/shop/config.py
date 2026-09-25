"""Application settings, loaded from environment variables.

Kept deliberately tiny. The point for this repo isn't pydantic-settings itself, it's
that `Settings` is a natural place to override values in tests (module 07) without
reaching for `monkeypatch.setenv` everywhere.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHOP_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./shop.db"
    payment_gateway_url: str = "https://payments.example.com"
    payment_gateway_api_key: str = "test-payment-gateway-key"
    redis_url: str = "redis://localhost:6379/0"
    tax_rate: float = 0.08  # 8%, applied to (subtotal - discount)
    api_key: str = "test-client-api-key"  # what *our* clients must send us, see api/deps.py


def get_settings() -> Settings:
    return Settings()
