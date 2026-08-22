from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from market_intelligence.selection.config import SelectionPolicy


@dataclass(slots=True)
class BuyerGroupPolicy:
    minimum: int = 0
    target: int = 0
    maximum: int = 0


def normalize_quotas(policy: SelectionPolicy) -> dict[str, BuyerGroupPolicy]:
    return {
        group: BuyerGroupPolicy(**values)
        for group, values in policy.buyer_group_quotas.items()
    }


def category_targets(policy: SelectionPolicy) -> dict[str, int]:
    return {
        group: values.get("target", 0)
        for group, values in policy.buyer_group_quotas.items()
    }


def policy_snapshot(policy: SelectionPolicy) -> dict[str, Any]:
    return {
        "target_size": policy.target_size,
        "minimum_opportunity_score": policy.minimum_opportunity_score,
        "minimum_confidence": policy.minimum_confidence,
        "minimum_evidence_coverage": policy.minimum_evidence_coverage,
        "max_category_share": policy.max_category_share,
        "max_per_niche": policy.max_per_niche,
        "max_problem_share": policy.max_problem_share,
        "quotas": policy.buyer_group_quotas,
    }
