from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.demand.service import DemandScoringService


def _product(name: str, *, niche: str | None = None, product_type: ProductType | None = None, review_count: int = 12, keywords: list[str] | None = None) -> Product:
    return Product(
        product_name=name,
        marketplace=Marketplace.MOCK,
        url=f"https://example.test/{name.lower().replace(' ', '-')}",
        collected_at=datetime.now(timezone.utc),
        external_id=name.lower().replace(' ', '-'),
        niche=niche,
        product_type=product_type,
        price=Decimal("9.99"),
        currency="USD",
        review_count=review_count,
        rating=4.6,
        keywords=keywords or [],
        description="Helps owners price products and manage costs.",
    )


def test_demand_score_ranks_better_cluster_signal_above_weak_signal():
    strong_cluster = ProductCluster(
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator", "costing"],
        product_count=6,
        confidence=0.82,
        members=[
            _product("Bakery Pricing Calculator", niche="bakery", product_type=ProductType.CALCULATOR, review_count=40, keywords=["bakery", "pricing", "calculator"]),
            _product("Bakery Costing Spreadsheet", niche="bakery", product_type=ProductType.SPREADSHEET, review_count=32, keywords=["bakery", "costing", "spreadsheet"]),
            _product("Custom Cake Pricing Workbook", niche="bakery", product_type=ProductType.TEMPLATE, review_count=28, keywords=["cake", "pricing", "workbook"]),
            _product("Bakery Inventory Tracker", niche="bakery", product_type=ProductType.TRACKER, review_count=18, keywords=["bakery", "inventory", "tracker"]),
            _product("Wedding Budget Planner", niche="wedding", product_type=ProductType.TEMPLATE, review_count=14, keywords=["budget", "planner"],),
            _product("Bakery Price Guide", niche="bakery", product_type=ProductType.TEMPLATE, review_count=11, keywords=["bakery", "price", "guide"]),
        ],
    )
    weak_cluster = ProductCluster(
        name="Generic Template",
        slug="generic-template",
        niche="misc",
        product_type="template",
        primary_problem=None,
        keywords=["template"],
        product_count=1,
        confidence=0.18,
        members=[_product("Simple Template", niche="misc", product_type=ProductType.TEMPLATE, review_count=2, keywords=["template"])],
    )

    service = DemandScoringService()
    strong_result = service.score_cluster(strong_cluster)
    weak_result = service.score_cluster(weak_cluster)

    assert 0.0 <= strong_result.demand_score <= 100.0
    assert 0.0 <= weak_result.demand_score <= 100.0
    assert strong_result.demand_score > weak_result.demand_score
    assert strong_result.evidence_coverage >= 0.5
    assert "bakery" in " ".join(strong_result.features["keywords"])


def test_demand_service_can_persist_run_and_scores():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    cluster = ProductCluster(
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
        product_count=3,
        confidence=0.75,
        members=[
            _product("Bakery Pricing Calculator", niche="bakery", product_type=ProductType.CALCULATOR, review_count=40),
            _product("Bakery Costing Spreadsheet", niche="bakery", product_type=ProductType.SPREADSHEET, review_count=32),
            _product("Cake Price Tracker", niche="bakery", product_type=ProductType.TRACKER, review_count=16),
        ],
    )

    saved_cluster = repository.save_cluster(cluster)
    result = DemandScoringService().calculate([saved_cluster])

    assert result.run.id is not None
    assert result.scores
    assert result.scores[0].id is not None
    assert result.scores[0].cluster_id == saved_cluster.id
    assert repository.latest_cluster_demand_score(saved_cluster.id) is not None
