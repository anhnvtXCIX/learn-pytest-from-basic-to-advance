"""Data builders. See modules/11-full-api-tests/README.md for the pattern -- a
`polyfactory` factory generalizes module 03's hand-rolled factory-as-fixture.
"""

from __future__ import annotations

from polyfactory.factories import DataclassFactory

from shop.domain.models import Product


class ProductFactory(DataclassFactory[Product]):
    __model__ = Product
