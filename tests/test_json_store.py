import json
from datetime import datetime, timezone
from decimal import Decimal

from crawler.models import Marketplace, Product, SearchResult
from crawler.storage.json_store import JsonResultStore


def test_json_store_serializes_canonical_result(tmp_path):
    timestamp = datetime(2026, 8, 20, 18, 0, tzinfo=timezone.utc)
    result = SearchResult(
        query="Bakery Pricing Calculator",
        marketplace=Marketplace.ETSY,
        collected_at=timestamp,
        products=[
            Product(
                id=1,
                external_id="123",
                product_name="Calculator",
                marketplace=Marketplace.ETSY,
                url="https://example.test/listing/1",
                price=Decimal("12.99"),
                currency="USD",
                review_count=532,
                query="Bakery Pricing Calculator",
                collected_at=timestamp,
                raw_product_id=8,
            )
        ],
    )

    path = JsonResultStore(tmp_path).save(result)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path == tmp_path / "etsy/bakery-pricing-calculator/2026-08-20T18-00-00.json"
    assert payload["products"][0]["product_name"] == "Calculator"
    assert payload["products"][0]["price"] == 12.99
    assert payload["products"][0]["raw_product_id"] == 8
