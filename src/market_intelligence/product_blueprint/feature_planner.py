from __future__ import annotations

from typing import Any

from market_intelligence.deep_research.models import DeepResearchDossier


def plan_features(dossier: DeepResearchDossier, thesis: Any | None = None) -> dict[str, list[str]]:
    feature_rows = (dossier.feature_matrix or {}).get("features") or []
    core: list[str] = []
    differentiation: list[str] = []
    for row in feature_rows:
        feature_name = str(row.get("feature", "")).replace("_", " ")
        coverage = float(row.get("coverage_ratio", 0.0) or 0.0)
        importance = float(row.get("importance", 0.0) or 0.0)
        if coverage >= 0.75:
            core.append(feature_name)
        elif importance >= 0.75:
            differentiation.append(feature_name)
    observed_gaps = list(dossier.observed_gaps or [])
    if observed_gaps:
        differentiation.extend(observed_gaps[:3])
    if not core:
        core = ["pricing input", "cost summary", "suggested price"]
    if not differentiation:
        differentiation = ["waste tracking", "labor costing", "packaging impact"]
    return {
        "core_features": core[:6],
        "differentiation_features": differentiation[:6],
    }
