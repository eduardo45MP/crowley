from __future__ import annotations

from typing import Any

from market_intelligence.editorial.models import CommercialPositioning


def derive_commercial_positioning(
    *,
    cluster: Any,
    buyer_group: str | None,
    thesis: Any | None,
    blueprint: Any | None,
    dossier: Any | None,
) -> CommercialPositioning:
    name = _first(_attr(blueprint, "product_name"), _attr(cluster, "name"))
    target = _first(_attr(thesis, "target_buyer"), _attr(blueprint, "target_buyer"), buyer_group, _attr(cluster, "niche"))
    pain = _first(_attr(thesis, "problem"), _attr(blueprint, "primary_problem"), _attr(cluster, "primary_problem"))
    value = _first(_attr(blueprint, "value_proposition"), _attr(thesis, "opportunity_statement"))
    proposed = list(_attr(thesis, "proposed_advantage") or [])
    blueprint_diff = list(_attr(blueprint, "differentiation_features") or [])
    research_diff = list(_attr(dossier, "differentiation_axes") or [])
    differentiator = _first(*(blueprint_diff + proposed + research_diff))
    benefit = value
    statement = None
    if name and target and pain and benefit:
        statement = f"For {target}, {name} addresses {pain} through {benefit}"
        if differentiator:
            statement += f", differentiated by {differentiator}"
        statement += "."
    return CommercialPositioning(
        suggested_product_name=name,
        target_buyer=target,
        pain=pain,
        benefit=benefit,
        primary_differentiator=differentiator,
        value_proposition=value,
        short_positioning_statement=statement,
    )


def _attr(value: Any | None, name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _first(*values: Any) -> str | None:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None
