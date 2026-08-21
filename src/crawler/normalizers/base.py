from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from crawler.models import Product, ProductType, RawMarketplaceProduct


class NormalizationError(ValueError):
    """A raw record cannot be represented as a canonical product."""


class ProductNormalizer(Protocol):
    def normalize(self, raw_product: RawMarketplaceProduct) -> Product: ...


def listing_age_days(listing_date: datetime | None, collected_at: datetime) -> int | None:
    if listing_date is None:
        return None
    if listing_date.tzinfo is None:
        listing_date = listing_date.replace(tzinfo=timezone.utc)
    return max(0, (collected_at.date() - listing_date.date()).days)


def controlled_product_type(value: object) -> ProductType | None:
    if value is None:
        return None
    try:
        return ProductType(str(value).strip().lower())
    except ValueError:
        return None

