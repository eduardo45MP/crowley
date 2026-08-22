from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.build_ease.features import BuildEaseFeatureExtractor
from market_intelligence.build_ease.scoring import BuildEaseScorer
from market_intelligence.build_ease.service import BuildEaseAnalysisService


def _product(name: str, **kwargs) -> Product:
    return Product(
        product_name=name,
        marketplace=Marketplace.MOCK,
        url=f"https://example.test/{name.lower().replace(' ', '-')}",
        collected_at=datetime.now(timezone.utc),
        external_id=name.lower().replace(' ', '-'),
        niche="bakery",
        product_type=ProductType.CALCULATOR,
        price=kwargs.get("price", Decimal("19.99")),
        currency="USD",
        review_count=kwargs.get("review_count", 50),
        rating=kwargs.get("rating", 4.7),
        seller=kwargs.get("seller", "demo-seller"),
        keywords=kwargs.get("keywords", ["bakery", "pricing", "calculator"]),
        description=kwargs.get("description", "Helps bakery owners set profitable prices."),
    )


def _cluster(*members: Product, **kwargs) -> ProductCluster:
    return ProductCluster(
        name=kwargs.get("name", "Bakery Pricing Calculator"),
        slug=kwargs.get("slug", "bakery-pricing-calculator"),
        niche=kwargs.get("niche", "bakery"),
        product_type=kwargs.get("product_type", "calculator"),
        primary_problem=kwargs.get("primary_problem", "pricing"),
        keywords=kwargs.get("keywords", ["bakery", "pricing", "calculator"]),
        product_count=len(members),
        confidence=0.82,
        members=list(members),
    )


def test_build_ease_high_for_simple_tools():
    simple_cluster = _cluster(
        _product("Bakery Pricing Calculator", keywords=["bakery", "pricing", "calculator"], description="Simple tool to calculate profit margin."),
        _product("Bakery Cost Calculator", keywords=["bakery", "cost", "calculator"], description="Quick cost estimator for recipes."),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
    )

    difficult_cluster = _cluster(
        _product("Dynamic Inventory + Pricing + Forecast Engine", keywords=["inventory", "pricing", "forecast", "api", "erp"], description="Requires real inventory feeds, forecasting rules, tax, margin, and external ERP integrations."),
        _product("Multi-Store Demand Planner", keywords=["inventory", "api", "erp", "forecast"], description="Complex planner with weather data, SKU drift, and external pricing synchronization."),
        name="Inventory Forecasting Platform",
        slug="inventory-forecasting-platform",
        niche="retail",
        product_type="tracker",
        primary_problem="inventory",
        keywords=["inventory", "forecast", "api", "erp"],
    )

    easy_score = BuildEaseScorer().score(BuildEaseFeatureExtractor().extract(simple_cluster))[0]
    difficult_score = BuildEaseScorer().score(BuildEaseFeatureExtractor().extract(difficult_cluster))[0]

    assert easy_score > difficult_score
    assert 0.0 <= easy_score <= 100.0
    assert 0.0 <= difficult_score <= 100.0


def test_repository_persists_build_ease_scores():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    cluster = _cluster(
        _product("Simple Pricing Calculator", keywords=["pricing", "calculator"], description="Quick margins and pricing helper."),
        _product("Margin Helper", keywords=["margin", "calculator"], description="Simple helper for bakery pricing decisions."),
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["pricing", "calculator"],
    )
    saved_cluster = repository.save_cluster(cluster)
    result = BuildEaseAnalysisService(repository=repository).analyze([saved_cluster])

    assert result.run.id is not None
    assert result.scores
    assert result.scores[0].id is not None
    assert result.scores[0].cluster_id == saved_cluster.id
    assert repository.latest_cluster_build_ease_score(saved_cluster.id) is not None
