from __future__ import annotations

from datetime import datetime, timezone

from crawler.models import Marketplace, RawMarketplaceProduct
from crawler.providers.base import MarketplaceProvider


class MockMarketplaceProvider(MarketplaceProvider):
    marketplace = Marketplace.MOCK

    def search(self, query: str, limit: int) -> list[RawMarketplaceProduct]:
        rows = [
            {
                "id": "bakery-pricing-calculator",
                "name": "  Bakery  Pricing Calculator ",
                "price_text": "$12.99",
                "reviews_text": "532 reviews",
                "rating_text": "4.9 / 5",
                "seller_name": " Crowley Test Shop ",
                "listing_url": "https://example.test/listing/bakery-pricing-calculator?utm_source=mock",
                "keywords": ["digital download", " Calculator ", "calculator"],
                "product_type": "calculator",
            },
            {
                "id": "cake-cost-spreadsheet",
                "name": "Cake Cost Spreadsheet",
                "price_text": "US$ 8.50",
                "reviews_text": "189",
                "rating_text": "4,8 stars",
                "seller_name": "Crowley Test Shop",
                "listing_url": "https://example.test/listing/cake-cost-spreadsheet?ref=search",
                "keywords": ["spreadsheet", "cake costing"],
                "product_type": "spreadsheet",
            },
            {
                "id": "baking-business-planner",
                "name": "Baking Business Planner",
                "price_text": "€9,50",
                "reviews_text": "2.1k",
                "rating_text": None,
                "seller_name": "Crowley Test Shop",
                "listing_url": "https://example.test/listing/baking-business-planner",
                "keywords": ["planner", "template"],
                "product_type": "template",
            },
        ]
        collected_at = datetime.now(timezone.utc)
        return [
            RawMarketplaceProduct(
                marketplace=self.marketplace,
                external_id=str(payload["id"]),
                query=query,
                raw_payload=payload,
                collected_at=collected_at,
            )
            for payload in rows[: max(0, limit)]
        ]

