from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_CURRENCY_MARKERS = (
    ("R$", "BRL"),
    ("US$", "USD"),
    ("CA$", "CAD"),
    ("A$", "AUD"),
    ("£", "GBP"),
    ("€", "EUR"),
    ("¥", "JPY"),
    ("$", "USD"),
)
_CURRENCY_CODES = ("USD", "EUR", "GBP", "BRL", "CAD", "AUD", "JPY")
_TRACKING_PARAMS = {
    "ref",
    "referrer",
    "campaign",
    "click_key",
    "click_sum",
    "ga_order",
    "ga_search_query",
    "ga_view_type",
    "ls",
    "organic_search_click",
}


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def parse_price(value: str | int | float | Decimal | None) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, Decimal):
        return value, None
    if isinstance(value, (int, float)):
        return Decimal(str(value)), None

    text = normalize_text(value) or ""
    upper = text.upper()
    currency = next((code for marker, code in _CURRENCY_MARKERS if marker in upper), None)
    if currency is None:
        currency = next((code for code in _CURRENCY_CODES if code in upper), None)

    match = re.search(r"\d[\d\s.,]*", text)
    if not match:
        return None, currency
    number = re.sub(r"\s", "", match.group())
    if "," in number and "." in number:
        decimal_separator = "," if number.rfind(",") > number.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        number = number.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif "," in number:
        parts = number.split(",")
        number = "".join(parts) if len(parts[-1]) == 3 else "".join(parts[:-1]) + "." + parts[-1]
    elif "." in number:
        parts = number.split(".")
        if len(parts) > 2 or len(parts[-1]) == 3:
            number = "".join(parts)
    try:
        return Decimal(number), currency
    except InvalidOperation:
        return None, currency


def parse_review_count(value: str | int | float | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = value.strip().lower().replace(" ", "")
    match = re.search(r"(\d[\d.,]*)([km])?", text)
    if not match:
        return None
    number, suffix = match.groups()
    if suffix:
        number = number.replace(",", ".")
        try:
            multiplier = 1_000 if suffix == "k" else 1_000_000
            return int(Decimal(number) * multiplier)
        except InvalidOperation:
            return None
    number = number.replace(",", "").replace(".", "")
    try:
        return int(number)
    except ValueError:
        return None


def parse_rating(value: str | int | float | Decimal | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace(",", ".")
    scale_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*([0-9]+(?:\.[0-9]+)?)", text)
    if scale_match:
        rating, scale = map(float, scale_match.groups())
        return rating if scale == 5 and 0 <= rating <= 5 else None
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
    if not match:
        return None
    rating = float(match.group())
    return rating if 0 <= rating <= 5 else None


def canonicalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMS
    ]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), ""))


def normalize_keywords(values: list[object] | tuple[object, ...] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        keyword = normalize_text(str(value))
        key = keyword.casefold() if keyword else ""
        if keyword and key not in seen:
            seen.add(key)
            normalized.append(keyword)
    return normalized
