from __future__ import annotations

from market_intelligence.selection.config import SelectionPolicy
from market_intelligence.selection.models import OpportunityCandidate
from market_intelligence.selection.service import PortfolioSelector


def _candidate(cluster_id: int, score: float, buyer_group: str = "small_business", niche: str = "bakery", problem_type: str = "pricing", product_type: str = "calculator") -> OpportunityCandidate:
    return OpportunityCandidate(
        cluster_id=cluster_id,
        cluster_name=f"Cluster {cluster_id}",
        opportunity_score=score,
        opportunity_confidence=0.8,
        evidence_coverage=0.7,
        buyer_group=buyer_group,
        niche=niche,
        problem_type=problem_type,
        product_type=product_type,
        demand_score=80.0,
        competition_score=60.0,
        purchase_intent_score=75.0,
        build_ease_score=80.0,
        differentiation_score=70.0,
        price_potential_score=70.0,
        ranking_eligible=True,
    )


def test_selection_keeps_target_size_and_quality_floor():
    policy = SelectionPolicy(target_size=5, minimum_opportunity_score=70.0, minimum_confidence=0.50, minimum_evidence_coverage=0.60)
    candidates = [
        _candidate(1, 95.0, "small_business", "bakery", "pricing", "calculator"),
        _candidate(2, 92.0, "small_business", "bakery", "pricing", "calculator"),
        _candidate(3, 90.0, "creators", "content", "planning", "tracker"),
        _candidate(4, 88.0, "creators", "content", "planning", "tracker"),
        _candidate(5, 85.0, "property_hospitality", "lodging", "budgeting", "spreadsheet"),
        _candidate(6, 81.0, "ecommerce_sellers", "shopify", "inventory", "tracker"),
    ]

    result = PortfolioSelector(policy=policy).select(candidates)

    assert result.run.selected_count == 5
    assert all(item.opportunity_score is not None and item.opportunity_score >= 70.0 for item in result.selected)
    assert len(result.selected) == 5


def test_selection_respects_buyer_group_quota_and_shortfall():
    policy = SelectionPolicy(target_size=4, buyer_group_quotas={"small_business": {"minimum": 1, "target": 2, "maximum": 2}, "other": {"minimum": 1, "target": 2, "maximum": 2}})
    candidates = [
        _candidate(1, 95.0, "small_business", "bakery", "pricing", "calculator"),
        _candidate(2, 93.0, "small_business", "bakery", "pricing", "calculator"),
        _candidate(3, 88.0, "other", "misc", "budgeting", "spreadsheet"),
        _candidate(4, 80.0, "other", "misc", "budgeting", "spreadsheet"),
    ]

    result = PortfolioSelector(policy=policy).select(candidates)

    assert result.run.selected_count == 4
    assert sum(1 for item in result.selected if item.buyer_group == "small_business") <= 2
    assert sum(1 for item in result.selected if item.buyer_group == "other") <= 2
