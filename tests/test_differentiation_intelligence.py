from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.differentiation.features import DifferentiationFeatureExtractor
from market_intelligence.differentiation.scoring import DifferentiationScorer
from market_intelligence.differentiation.service import DifferentiationAnalysisService


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


def test_differentiation_high_for_under_served_market():
    underserved = _cluster(
        _product("Simple Margin Calculator", keywords=["pricing", "margin", "calculator"], description="Basic spreadsheet for margin checks."),
        _product("Bakery Price Checker", keywords=["pricing", "cost", "calculator"], description="Simple tool to estimate costs."),
        name="Bakery Pricing Tools",
        slug="bakery-pricing-tools",
        primary_problem="pricing",
        keywords=["pricing", "bakery", "calculator"],
    )
    mature = _cluster(
        _product("Bakery Profit OS", keywords=["pricing", "forecast", "dashboard", "automation", "api"], description="Advanced bakery pricing dashboard with forecast, exports, ERP sync, onboarding, and custom templates."),
        _product("Inventory & Pricing Studio", keywords=["pricing", "inventory", "dashboard", "automation", "api"], description="Inventory-aware automated pricing suite with docs, onboarding, and internationalization."),
        name="Bakery Pricing Platforms",
        slug="bakery-pricing-platforms",
        primary_problem="pricing",
        keywords=["pricing", "forecast", "dashboard", "automation", "api"],
    )

    underserved_score = DifferentiationScorer().score(DifferentiationFeatureExtractor().extract(underserved))[0]
    mature_score = DifferentiationScorer().score(DifferentiationFeatureExtractor().extract(mature))[0]

    assert underserved_score > mature_score
    assert 0.0 <= underserved_score <= 100.0
    assert 0.0 <= mature_score <= 100.0


def test_repository_persists_differentiation_scores():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    cluster = _cluster(
        _product("Basic Pricing Helper", keywords=["pricing", "calculator"], description="Quick price helper with no onboarding or automation."),
        _product("Margin Estimator", keywords=["margin", "calculator"], description="Simple calculator for margin planning."),
        name="Bakery Pricing Helpers",
        slug="bakery-pricing-helpers",
        primary_problem="pricing",
        keywords=["pricing", "calculator"],
    )
    saved_cluster = repository.save_cluster(cluster)
    result = DifferentiationAnalysisService(repository=repository).analyze([saved_cluster])

    assert result.run.id is not None
    assert result.scores
    assert result.scores[0].id is not None
    assert result.scores[0].cluster_id == saved_cluster.id
    assert repository.latest_cluster_differentiation_score(saved_cluster.id) is not None
