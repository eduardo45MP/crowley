from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any


class Marketplace(StrEnum):
    ETSY = "etsy"
    GUMROAD = "gumroad"
    CREATIVE_MARKET = "creative_market"
    MOCK = "mock"


class ProductType(StrEnum):
    SPREADSHEET = "spreadsheet"
    CALCULATOR = "calculator"
    TRACKER = "tracker"
    TEMPLATE = "template"
    UNKNOWN = "unknown"


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


@dataclass(slots=True)
class RawMarketplaceProduct:
    marketplace: Marketplace
    raw_payload: dict[str, Any]
    collected_at: datetime
    external_id: str | None = None
    query: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(slots=True)
class Product:
    product_name: str
    marketplace: Marketplace
    url: str
    collected_at: datetime
    id: int | None = None
    external_id: str | None = None
    niche: str | None = None
    product_type: ProductType | None = None
    price: Decimal | None = None
    currency: str | None = None
    review_count: int | None = None
    rating: float | None = None
    seller: str | None = None
    keywords: list[str] = field(default_factory=list)
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)
    category: str | None = None
    listing_date: datetime | None = None
    listing_age_days: int | None = None
    query: str | None = None
    raw_product_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def title(self) -> str:
        """Read-only V1 compatibility alias."""
        return self.product_name

    @property
    def tags(self) -> list[str]:
        """Read-only V1 compatibility alias."""
        return self.keywords

    @property
    def marketplace_id(self) -> str | None:
        """Read-only V1 compatibility alias."""
        return self.external_id

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(slots=True)
class SearchResult:
    query: str
    marketplace: Marketplace
    collected_at: datetime
    products: list[Product] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "marketplace": self.marketplace.value,
            "collected_at": self.collected_at.isoformat(),
            "products": [product.to_dict() for product in self.products],
        }

