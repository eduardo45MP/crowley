from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.purchase_intent.features import PurchaseIntentFeatureExtractor
from market_intelligence.purchase_intent.scoring import PurchaseIntentScorer
from market_intelligence.purchase_intent.service import PurchaseIntentAnalysisService


def _product(name: str, *, seller: str | None = None, price: Decimal | None = None, review_count: int | None = None, rating: float | None = None, keywords: list[str] | None = None) -> Product:
    return Product(
        product_name=name,
        marketplace=Marketplace.MOCK,
        url=f"https://example.test/{name.lower().replace(' ', '-')}",
        collected_at=datetime.now(timezone.utc),
        external_id=name.lower().replace(' ', '-'),
        niche="bakery",
        product_type=ProductType.CALCULATOR,
        price=price,
        currency="USD" if price is not None else None,
        review_count=review_count,
        rating=rating,
        seller=seller,
        keywords=keywords or ["bakery", "pricing", "calculator"],
        description="Helps bakery owners set profitable prices and protect margins.",
    )


def _cluster(*members: Product, **kwargs) -> ProductCluster:
    return ProductCluster(
        name=kwargs.get("name", "Bakery Pricing Calculators"),
        slug=kwargs.get("slug", "bakery-pricing-calculators"),
        niche=kwargs.get("niche", "bakery"),
        product_type=kwargs.get("product_type", "calculator"),
        primary_problem=kwargs.get("primary_problem", "pricing"),
        keywords=kwargs.get("keywords", ["bakery", "pricing", "calculator"]),
        product_count=len(members),
        confidence=0.82,
        members=list(members),
    )


def test_purchase_intent_score_is_higher_for_financially_important_problems():
    pricing_cluster = _cluster(
        _product("Bakery Pricing Calculator", price=Decimal("19.99"), review_count=200, rating=4.8, keywords=["bakery", "pricing", "calculator"]),
        _product("Bakery Costing Spreadsheet", price=Decimal("29.99"), review_count=180, rating=4.6, keywords=["bakery", "costing", "spreadsheet"]),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["pricing", "bakery", "calculator"],
    )
    generic_cluster = _cluster(
        _product("Pretty Ideas Organizer", price=Decimal("14.99"), review_count=50, rating=4.5, keywords=["ideas", "planner"]) ,
        _product("Daily Mood Planner", price=Decimal("9.99"), review_count=40, rating=4.4, keywords=["planner", "mood"]),
        name="Pretty Ideas Organizer",
        slug="pretty-ideas-organizer",
        niche="planning",
        product_type="planner",
        primary_problem="planning",
        keywords=["planner", "ideas"],
    )

    pricing_score = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(pricing_cluster))[0]
    generic_score = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(generic_cluster))[0]

    assert pricing_score > generic_score
    assert 0.0 <= pricing_score <= 100.0
    assert 0.0 <= generic_score <= 100.0


def test_purchase_intent_is_independent_of_demand_signals():
    cluster_one = _cluster(
        _product("Bakery Pricing Calculator", price=Decimal("19.99"), review_count=1000, rating=4.8),
        _product("Bakery Costing Spreadsheet", price=Decimal("24.99"), review_count=900, rating=4.6),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        product_type="calculator",
        primary_problem="pricing",
    )
    cluster_two = _cluster(
        _product("Bakery Pricing Calculator", price=Decimal("19.99"), review_count=10, rating=4.8),
        _product("Bakery Costing Spreadsheet", price=Decimal("24.99"), review_count=9, rating=4.6),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        product_type="calculator",
        primary_problem="pricing",
    )

    score_one = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(cluster_one))[0]
    score_two = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(cluster_two))[0]
    assert abs(score_one - score_two) < 10.0


def test_repository_persists_purchase_intent_runs_and_scores():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    cluster = _cluster(
        _product("Bakery Pricing Calculator", price=Decimal("19.99"), review_count=250, rating=4.8),
        _product("Bakery Costing Spreadsheet", price=Decimal("29.99"), review_count=180, rating=4.6),
        _product("Bakery Margin Planner", price=Decimal("39.99"), review_count=120, rating=4.5),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        product_type="calculator",
        primary_problem="pricing",
    )
    saved_cluster = repository.save_cluster(cluster)
    result = PurchaseIntentAnalysisService(repository=repository).analyze([saved_cluster])

    assert result.run.id is not None
    assert result.scores
    assert result.scores[0].id is not None
    assert result.scores[0].cluster_id == saved_cluster.id
    assert repository.latest_cluster_purchase_intent_score(saved_cluster.id) is not None


def test_llm_substitutability_penalizes_generic_or_easy_to_replace_problems():
    generic_cluster = _cluster(
        _product("Content Idea Tracker", price=Decimal("9.99"), review_count=70, rating=4.6, keywords=["content", "idea", "tracker"]),
        name="Content Idea Tracker",
        slug="content-idea-tracker",
        niche="content",
        product_type="tracker",
        primary_problem="planning",
        keywords=["content", "idea", "tracker"],
    )
    pricing_cluster = _cluster(
        _product("Pricing Calculator", price=Decimal("25.00"), review_count=80, rating=4.7, keywords=["pricing", "calculator"]),
        name="Pricing Calculator",
        slug="pricing-calculator",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["pricing", "calculator"],
    )

    generic_score = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(generic_cluster))[0]
    pricing_score = PurchaseIntentScorer().score(PurchaseIntentFeatureExtractor().extract(pricing_cluster))[0]

    assert pricing_score > generic_score
