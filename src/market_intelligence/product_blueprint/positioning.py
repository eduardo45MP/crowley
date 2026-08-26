from __future__ import annotations

from typing import Any


def derive_positioning(cluster_name: str, thesis: Any | None = None, dossier: Any | None = None) -> dict[str, str | list[str]]:
    name = cluster_name or "Product"
    target_buyer = "small operators and independent creators" if "bakery" in name.lower() else "operators with recurring pricing decisions"
    primary_promise = "simplify the cost-to-price workflow" if "pricing" in name.lower() else "make complex calculations understandable"
    differentiation_claim = "more complete than spreadsheet-only pricing tools" if thesis is not None else "clearer workflow logic and cost assumptions"
    positioning_keywords = ["pricing", "costs", "margin", "workflow"]
    if dossier is not None:
        for gap in (dossier.observed_gaps or [])[:2]:
            positioning_keywords.append(gap.lower().replace(" ", "_"))
    return {
        "target_buyer": target_buyer,
        "primary_promise": primary_promise,
        "primary_problem": "price decisions are too manual and incomplete",
        "differentiation_claim": differentiation_claim,
        "positioning_keywords": sorted(set(positioning_keywords)),
    }
