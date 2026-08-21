from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crawler.normalization import (
    canonicalize_url,
    normalize_keywords,
    normalize_text,
    parse_price,
    parse_rating,
    parse_review_count,
)


def test_product_name_normalization_preserves_content_and_capitalization():
    assert normalize_text("  PRO Bakery\n  Calculator Bundle ") == "PRO Bakery Calculator Bundle"


@pytest.mark.parametrize(
    ("raw", "price", "currency"),
    [
        ("$12.99", Decimal("12.99"), "USD"),
        ("US$ 12.99", Decimal("12.99"), "USD"),
        ("USD 1,299.00", Decimal("1299.00"), "USD"),
        ("€9,50", Decimal("9.50"), "EUR"),
        ("£14.00", Decimal("14.00"), "GBP"),
        ("12.99", Decimal("12.99"), None),
    ],
)
def test_price_normalization(raw, price, currency):
    assert parse_price(raw) == (price, currency)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("532", 532), ("532 reviews", 532), ("1,234", 1234), ("1.2k", 1200), ("2.5K reviews", 2500)],
)
def test_review_count_normalization(raw, expected):
    assert parse_review_count(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("4.9", 4.9), ("4.9 / 5", 4.9), ("4,8 stars", 4.8), ("8 / 10", None), ("unknown", None)],
)
def test_rating_normalization(raw, expected):
    assert parse_rating(raw) == expected


def test_url_removes_only_tracking_and_preserves_listing_parameters():
    value = "HTTPS://Example.COM/p/1?utm_source=x&variation=42&ref=search#reviews"
    assert canonicalize_url(value) == "https://example.com/p/1?variation=42"


def test_keywords_are_cleaned_and_case_insensitively_deduplicated():
    assert normalize_keywords([" Bakery ", "bakery", "PRICE  Calculator", "", "  "]) == [
        "Bakery",
        "PRICE Calculator",
    ]


def test_missing_values_stay_unknown():
    assert parse_price(None) == (None, None)
    assert parse_review_count(None) is None
    assert parse_rating(None) is None
    assert normalize_text(None) is None
    assert normalize_keywords(None) == []


def test_datetime_fixture_is_timezone_aware():
    assert datetime(2026, 8, 20, tzinfo=timezone.utc).tzinfo is not None

