from __future__ import annotations

from market_intelligence.opportunity.config import OpportunityScoreConfig
from market_intelligence.opportunity.models import OpportunityInputs
from market_intelligence.opportunity.scoring import OpportunityScorer


def test_opportunity_formula_matches_weighted_total():
    inputs = OpportunityInputs(
        cluster_id=1,
        demand_score=88.0,
        purchase_intent_score=95.0,
        competition_score=65.0,
        differentiation_score=85.0,
        build_ease_score=92.0,
        price_potential_score=70.0,
    )

    result = OpportunityScorer().score(inputs)

    assert result.opportunity_score is not None
    assert abs(result.opportunity_score - 84.1) < 1e-9
    assert result.status == "complete"
    assert result.dimension_coverage == 1.0


def test_all_zeros_and_ones_are_normalized():
    scorer = OpportunityScorer()

    zeroed = OpportunityInputs(cluster_id=1, demand_score=0.0, purchase_intent_score=0.0, competition_score=0.0, differentiation_score=0.0, build_ease_score=0.0, price_potential_score=0.0)
    all_hundred = OpportunityInputs(cluster_id=1, demand_score=100.0, purchase_intent_score=100.0, competition_score=100.0, differentiation_score=100.0, build_ease_score=100.0, price_potential_score=100.0)
    assert scorer.score(zeroed).opportunity_score == 0.0
    assert scorer.score(all_hundred).opportunity_score == 100.0


def test_missing_price_potential_is_provisional():
    inputs = OpportunityInputs(
        cluster_id=1,
        demand_score=88.0,
        purchase_intent_score=95.0,
        competition_score=65.0,
        differentiation_score=85.0,
        build_ease_score=92.0,
        price_potential_score=None,
    )

    result = OpportunityScorer().score(inputs)

    assert result.status == "provisional"
    assert result.dimension_coverage == 0.9
    assert result.opportunity_score is not None
    assert result.qualification in {"strong", "interesting"}


def test_insufficient_coverage_fails():
    inputs = OpportunityInputs(cluster_id=1, demand_score=60.0, purchase_intent_score=55.0, competition_score=None, differentiation_score=None, build_ease_score=None, price_potential_score=None)

    result = OpportunityScorer().score(inputs)

    assert result.status == "insufficient_data"
    assert result.opportunity_score is None


def test_none_and_zero_are_distinct():
    missing = OpportunityInputs(cluster_id=1, demand_score=50.0, purchase_intent_score=50.0, competition_score=50.0, differentiation_score=50.0, build_ease_score=50.0, price_potential_score=None)
    zero_value = OpportunityInputs(cluster_id=1, demand_score=50.0, purchase_intent_score=50.0, competition_score=50.0, differentiation_score=50.0, build_ease_score=50.0, price_potential_score=0.0)

    result_missing = OpportunityScorer().score(missing)
    result_zero = OpportunityScorer().score(zero_value)

    assert result_missing.status == "provisional"
    assert result_zero.status == "complete"
    assert result_missing.opportunity_score != result_zero.opportunity_score


def test_invalid_weights_rejected():
    try:
        OpportunityScoreConfig(demand_weight=0.2, purchase_intent_weight=0.2, competition_weight=0.2, differentiation_weight=0.2, build_ease_weight=0.1, price_potential_weight=0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("weights should fail when they do not sum to 1.0")


def test_fatal_weakness_and_bottleneck_are_reported():
    inputs = OpportunityInputs(
        cluster_id=1,
        demand_score=20.0,
        purchase_intent_score=100.0,
        competition_score=100.0,
        differentiation_score=100.0,
        build_ease_score=100.0,
        price_potential_score=100.0,
    )

    result = OpportunityScorer().score(inputs)

    assert "demand" in result.bottlenecks
    assert result.fatal_weaknesses
    assert result.qualification in {"weak", "speculative"}
