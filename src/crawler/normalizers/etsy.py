from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from crawler.models import Marketplace, Product, RawMarketplaceProduct
from crawler.normalization import (
    canonicalize_url,
    normalize_keywords,
    normalize_text,
    parse_rating,
    parse_review_count,
)
from crawler.normalizers.base import NormalizationError, controlled_product_type, listing_age_days


class EtsyProductNormalizer:
    def normalize(self, raw_product: RawMarketplaceProduct) -> Product:
        if raw_product.marketplace is not Marketplace.ETSY:
            raise NormalizationError("EtsyProductNormalizer recebeu marketplace incompatível")
        payload = raw_product.raw_payload
        product_name = normalize_text(_string(payload.get("title")))
        url = canonicalize_url(_string(payload.get("url")) or "")
        if not product_name or not url:
            raise NormalizationError("Listing Etsy sem title ou url")

        price, currency = _etsy_money(payload.get("price"))
        listing_date = _timestamp(
            payload.get("original_creation_timestamp") or payload.get("creation_timestamp")
        )
        images = payload.get("images") if isinstance(payload.get("images"), list) else []
        image_urls = [
            str(image.get("url_fullxfull") or image.get("url_570xN"))
            for image in images
            if isinstance(image, dict) and (image.get("url_fullxfull") or image.get("url_570xN"))
        ]
        return Product(
            product_name=product_name,
            marketplace=Marketplace.ETSY,
            url=url,
            collected_at=raw_product.collected_at,
            external_id=raw_product.external_id,
            niche=None,
            product_type=controlled_product_type(payload.get("product_type")),
            price=price,
            currency=currency,
            review_count=parse_review_count(payload.get("review_count")),
            rating=parse_rating(payload.get("rating")),
            seller=normalize_text(_string(payload.get("shop_name") or payload.get("seller"))),
            keywords=normalize_keywords(payload.get("tags") if isinstance(payload.get("tags"), list) else []),
            description=normalize_text(_string(payload.get("description"))),
            image_urls=[canonicalize_url(url) for url in image_urls],
            category=normalize_text(_string(payload.get("category"))),
            listing_date=listing_date,
            listing_age_days=listing_age_days(listing_date, raw_product.collected_at),
            query=raw_product.query,
            raw_product_id=raw_product.id,
        )


def _etsy_money(value: object) -> tuple[Decimal | None, str | None]:
    if not isinstance(value, dict):
        return None, None
    amount = value.get("amount")
    divisor = value.get("divisor") or 100
    currency = normalize_text(_string(value.get("currency_code")))
    try:
        price = Decimal(str(amount)) / Decimal(str(divisor)) if amount is not None else None
    except (InvalidOperation, ZeroDivisionError):
        price = None
    return price, currency.upper() if currency else None


def _timestamp(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc) if value is not None else None
    except (TypeError, ValueError, OSError):
        return None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None

