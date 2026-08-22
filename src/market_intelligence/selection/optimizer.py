from __future__ import annotations

from typing import Iterable

from market_intelligence.selection.models import OpportunityCandidate


def candidate_quality_score(candidate: OpportunityCandidate) -> float:
    score = float(candidate.opportunity_score or 0.0)
    confidence = float(candidate.opportunity_confidence or 0.0)
    evidence = float(candidate.evidence_coverage or 0.0)
    return score + (confidence * 15.0) + (evidence * 10.0)


def diversity_bonus(candidate: OpportunityCandidate, selected: Iterable[OpportunityCandidate]) -> float:
    selected_items = list(selected)
    bonus = 0.0
    qualities = {
        "buyer_group": candidate.buyer_group,
        "niche": candidate.niche,
        "problem_type": candidate.problem_type,
        "product_type": candidate.product_type,
    }
    for name, value in qualities.items():
        if value is None:
            continue
        current = sum(1 for item in selected_items if getattr(item, name, None) == value)
        if current == 0:
            bonus += 2.0
        elif current == 1:
            bonus += 0.75
        else:
            bonus -= 0.5 * current
    return bonus


def selection_utility(candidate: OpportunityCandidate, selected: list[OpportunityCandidate]) -> float:
    return candidate_quality_score(candidate) + diversity_bonus(candidate, selected)
