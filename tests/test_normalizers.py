import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from crawler.models import Marketplace, ProductType, RawMarketplaceProduct
from crawler.normalizers.etsy import EtsyProductNormalizer
from crawler.normalizers.mock import MockProductNormalizer
from crawler.providers.mock import MockMarketplaceProvider


FIXTURES = Path(__file__).parent / "fixtures"


def test_etsy_fixture_becomes_expected_canonical_product():
    payload = json.loads((FIXTURES / "etsy/bakery_pricing.json").read_text(encoding="utf-8"))
    raw = RawMarketplaceProduct(
        id=7,
        marketplace=Marketplace.ETSY,
        external_id=str(payload["listing_id"]),
        query="bakery pricing calculator",
        raw_payload=payload,
        collected_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )

    product = EtsyProductNormalizer().normalize(raw)

    assert product.product_name == "Bakery Pricing Calculator"
    assert product.external_id == "123456789"
    assert product.price == Decimal("12.99")
    assert product.currency == "USD"
    assert product.review_count == 1234
    assert product.rating == 4.9
    assert product.seller == "Baking Tools Studio"
    assert product.url.endswith("?variation=42")
    assert product.keywords == ["Bakery", "pricing calculator"]
    assert product.product_type is ProductType.CALCULATOR
    assert product.niche is None
    assert product.raw_product_id == 7


def test_mock_provider_uses_real_raw_to_normalizer_pipeline():
    raw = MockMarketplaceProvider().search("bakery pricing calculator", 1)[0]
    assert isinstance(raw, RawMarketplaceProduct)
    assert raw.raw_payload["price_text"] == "$12.99"

    product = MockProductNormalizer().normalize(raw)

    assert product.product_name == "Bakery Pricing Calculator"
    assert product.price == Decimal("12.99")
    assert product.review_count == 532
    assert product.rating == 4.9
    assert product.keywords == ["digital download", "Calculator"]


def test_mock_normalizer_preserves_missing_fields_as_none_or_empty_lists():
    raw = RawMarketplaceProduct(
        marketplace=Marketplace.MOCK,
        external_id=None,
        query=None,
        raw_payload={"name": "Minimal", "listing_url": "https://example.test/minimal"},
        collected_at=datetime.now(timezone.utc),
    )

    product = MockProductNormalizer().normalize(raw)

    assert product.price is None
    assert product.currency is None
    assert product.review_count is None
    assert product.rating is None
    assert product.seller is None
    assert product.niche is None
    assert product.product_type is None
    assert product.keywords == []
    assert product.image_urls == []

