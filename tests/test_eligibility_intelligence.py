from __future__ import annotations

from crawler.clustering import ProductCluster
from market_intelligence.eligibility.service import EligibilityService
from market_intelligence.opportunity.models import OpportunityAnalysis


def _opportunity(cluster_id: int = 1, score: float = 85.0) -> OpportunityAnalysis:
    return OpportunityAnalysis(
        cluster_id=cluster_id,
        opportunity_score=score,
        status="complete",
        qualification="strong",
        opportunity_confidence=0.8,
        dimension_coverage=1.0,
        evidence_coverage=0.8,
        components={
            "demand": 80.0,
            "purchase_intent": 82.0,
            "competition": 68.0,
            "differentiation": 74.0,
            "build_ease": 83.0,
            "price_potential": 70.0,
        },
        source_analysis_ids={
            "demand": 1,
            "purchase_intent": 2,
            "competition": 3,
            "differentiation": 4,
            "build_ease": 5,
            "price_potential": 6,
        },
        source_model_versions={
            "demand": "demand-v1",
            "purchase_intent": "purchase-intent-v1",
            "competition": "competition-v1",
            "differentiation": "differentiation-v1",
            "build_ease": "build-ease-v1",
            "price_potential": "price-potential-v1",
        },
        bottlenecks=[],
        strongest_dimension="demand",
        weakest_dimension="price_potential",
        fatal_weaknesses=[],
        ranking_eligible=True,
        model_version="opportunity-v1",
        warnings=[],
    )


def test_medical_advice_gate_blocks():
    cluster = ProductCluster(
        name="Insulin Dose Calculator",
        slug="insulin-dose-calculator",
        niche="healthcare",
        product_type="calculator",
        primary_problem="diagnosis",
        secondary_problems=["treatment recommendation", "medical risk assessment"],
        keywords=["insulin", "dosage", "health", "medical"],
    )

    result = EligibilityService().evaluate_cluster(cluster, opportunity=_opportunity(score=91.0))

    assert result.status == "ineligible"
    assert result.ranking_eligible is False
    assert "regulated_medical_advice" in result.blocking_reasons


def test_low_demand_gate_blocks_and_preserves_score():
    cluster = ProductCluster(
        name="Niche Custom Template",
        slug="niche-custom-template",
        niche="unknown",
        product_type="template",
        primary_problem="planning",
        keywords=["template", "planning"],
    )
    opportunity = _opportunity(score=88.0)

    result = EligibilityService().evaluate_cluster(
        cluster,
        opportunity=opportunity,
        demand_score=15.0,
        demand_confidence=0.8,
    )

    assert result.status == "ineligible"
    assert result.ranking_eligible is False
    assert "minimum_demand" in result.blocking_reasons
    assert opportunity.opportunity_score == 88.0


def test_low_confidence_demand_requires_review():
    cluster = ProductCluster(
        name="Bakery Pricing Calculator",
        slug="bakery-pricing-calculator",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
    )

    result = EligibilityService().evaluate_cluster(
        cluster,
        opportunity=_opportunity(score=84.1),
        demand_score=50.0,
        demand_confidence=0.12,
        competition_score=60.0,
        differentiation_score=80.0,
        build_ease_score=80.0,
    )

    assert result.status == "review_required"
    assert result.ranking_eligible is False
    assert "demand_confidence" in result.review_reasons


def test_eligible_cluster_passes_gates():
    cluster = ProductCluster(
        name="Bakery Pricing Calculator",
        slug="bakery-pricing-calculator",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
    )

    result = EligibilityService().evaluate_cluster(
        cluster,
        opportunity=_opportunity(score=84.1),
        demand_score=80.0,
        demand_confidence=0.8,
        competition_score=60.0,
        differentiation_score=78.0,
        build_ease_score=82.0,
    )

    assert result.status == "eligible"
    assert result.ranking_eligible is True
    assert result.blocking_reasons == []
