from __future__ import annotations

from crawler.models import Marketplace, Product, RawMarketplaceProduct
from crawler.normalization import (
    canonicalize_url,
    normalize_keywords,
    normalize_text,
    parse_price,
    parse_rating,
    parse_review_count,
)
from crawler.normalizers.base import NormalizationError, controlled_product_type


class MockProductNormalizer:
    def normalize(self, raw_product: RawMarketplaceProduct) -> Product:
        if raw_product.marketplace is not Marketplace.MOCK:
            raise NormalizationError("MockProductNormalizer recebeu marketplace incompatível")
        payload = raw_product.raw_payload
        product_name = normalize_text(_text(payload.get("name")))
        url = canonicalize_url(_text(payload.get("listing_url")) or "")
        if not product_name or not url:
            raise NormalizationError("Listing mock sem name ou listing_url")
        price, currency = parse_price(_text(payload.get("price_text")))
        return Product(
            product_name=product_name,
            marketplace=Marketplace.MOCK,
            url=url,
            collected_at=raw_product.collected_at,
            external_id=raw_product.external_id,
            niche=None,
            product_type=controlled_product_type(payload.get("product_type")),
            price=price,
            currency=currency,
            review_count=parse_review_count(payload.get("reviews_text")),
            rating=parse_rating(payload.get("rating_text")),
            seller=normalize_text(_text(payload.get("seller_name"))),
            keywords=normalize_keywords(
                payload.get("keywords") if isinstance(payload.get("keywords"), list) else []
            ),
            description=normalize_text(_text(payload.get("description"))),
            image_urls=normalize_keywords(
                payload.get("image_urls") if isinstance(payload.get("image_urls"), list) else []
            ),
            category=normalize_text(_text(payload.get("category"))),
            listing_date=None,
            listing_age_days=None,
            query=raw_product.query,
            raw_product_id=raw_product.id,
        )


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None

