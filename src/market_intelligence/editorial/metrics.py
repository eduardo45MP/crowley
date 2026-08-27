from __future__ import annotations

from market_intelligence.editorial.models import PricingSummary


PRICING_MODEL_VERSION = "editorial-pricing-v1"
REVENUE_EFFICIENCY_MODEL_VERSION = "revenue-efficiency-v1"


def summarize_pricing(pricing_analysis: dict | None) -> PricingSummary:
    """Keep observed prices separate from a deterministic editorial recommendation.

    The recommendation is 110% of the observed median, bounded by the observed
    minimum and maximum. It is a positioning heuristic, not willingness-to-pay.
    """
    source = pricing_analysis or {}
    minimum = _number(source.get("minimum"))
    median = _number(source.get("median"))
    maximum = _number(source.get("maximum"))
    recommended = None
    if median is not None:
        recommended = round(median * 1.10, 2)
        if minimum is not None:
            recommended = max(minimum, recommended)
        if maximum is not None:
            recommended = min(maximum, recommended)
        recommended = round(recommended, 2)
    return PricingSummary(
        minimum_observed_price=minimum,
        median_observed_price=median,
        maximum_observed_price=maximum,
        recommended_price=recommended,
        currency=source.get("currency") or None,
    )


def revenue_efficiency_score(opportunity_score: float | None, build_hours: float | None) -> float | None:
    """Normalize opportunity/build effort to 0-100 for comparison, not forecasting.

    Formula: 100 * opportunity / (opportunity + 2 * max(hours, 1)).
    It is monotonic in both inputs and safely handles zero effort.
    """
    if opportunity_score is None or build_hours is None:
        return None
    opportunity = max(0.0, min(100.0, float(opportunity_score)))
    effort = max(1.0, float(build_hours))
    denominator = opportunity + (2.0 * effort)
    if denominator <= 0.0:
        return 0.0
    return round(max(0.0, min(100.0, 100.0 * opportunity / denominator)), 2)


def _number(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
