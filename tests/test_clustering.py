from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from crawler.clustering import ProductClusterFeatures, TfidfSimilarityEngine, build_clustering_text
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from crawler.services.clustering_service import ProductClusteringService


def _product(
    name: str,
    *,
    niche: str | None = None,
    product_type: ProductType | None = None,
    keywords: list[str] | None = None,
    description: str | None = None,
    category: str | None = None,
    marketplace: Marketplace = Marketplace.MOCK,
    external_id: str | None = None,
) -> Product:
    return Product(
        product_name=name,
        marketplace=marketplace,
        url=f"https://example.test/{(external_id or name).lower().replace(' ', '-')}",
        collected_at=datetime.now(timezone.utc),
        external_id=external_id or name.lower().replace(' ', '-'),
        niche=niche,
        product_type=product_type,
        price=Decimal("9.99"),
        currency="USD",
        keywords=keywords or [],
        description=description or "",
        category=category,
    )


def test_build_clustering_text_removes_noise_and_preserves_semantic_terms():
    product = _product(
        "Ultimate Bakery Pricing Spreadsheet Template 2026 - Instant Download",
        niche="bakery",
        product_type=ProductType.SPREADSHEET,
        keywords=["bakery", "pricing", "spreadsheet", "template"],
        description="Custom bakery pricing spreadsheet for home bakers.",
    )

    text = build_clustering_text(product)
    assert "bakery" in text
    assert "pricing" in text
    assert "spreadsheet" in text
    assert "instant" not in text
    assert "template" not in text or "spreadsheet" in text


def test_tfidf_similarity_groups_related_products_and_separates_unrelated_ones():
    bakery_a = _product(
        "Cake Pricing Calculator for Home Bakers",
        niche="bakery",
        product_type=ProductType.CALCULATOR,
        keywords=["bakery", "pricing", "calculator"],
        description="Cake pricing calculator for bakery owners.",
    )
    bakery_b = _product(
        "Bakery Costing Spreadsheet for Custom Cakes",
        niche="bakery",
        product_type=ProductType.SPREADSHEET,
        keywords=["bakery", "costing", "spreadsheet"],
        description="Bakery pricing and costing spreadsheet.",
    )
    tattoo = _product(
        "Tattoo Appointment Tracker",
        niche="tattoo",
        product_type=ProductType.TRACKER,
        keywords=["tattoo", "appointment", "tracker"],
    )

    engine = TfidfSimilarityEngine()
    engine.fit([bakery_a, bakery_b, tattoo])
    related = engine.similarity(bakery_a, bakery_b)
    unrelated = engine.similarity(bakery_a, tattoo)

    assert related > 0.45
    assert unrelated < related


def test_cluster_service_creates_market_coherent_clusters_from_fixture():
    fixture = Path(__file__).parent / "fixtures" / "clustering" / "products.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    products = [
        Product(
            product_name=item["product_name"],
            marketplace=Marketplace(item["marketplace"]),
            url=item["url"],
            collected_at=datetime.now(timezone.utc),
            external_id=item["external_id"],
            niche=item.get("niche"),
            product_type=ProductType(item["product_type"]) if item.get("product_type") else None,
            price=Decimal(str(item.get("price", "9.99"))),
            currency=item.get("currency", "USD"),
            review_count=item.get("review_count"),
            rating=item.get("rating"),
            seller=item.get("seller"),
            keywords=item.get("keywords", []),
            description=item.get("description"),
            category=item.get("category"),
        )
        for item in payload
    ]

    run = ProductClusteringService(similarity_threshold=0.55, minimum_cluster_size=2).cluster_products(products)
    names = [cluster.name for cluster in run.clusters]

    assert any("Bakery Pricing" in name for name in names)
    assert any("Airbnb ROI" in name for name in names)
    assert any("Wedding Budget" in name for name in names)
    assert any("Tattoo Artist" in name for name in names)


def test_repository_persists_cluster_runs_memberships_and_clusters():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    cluster_a = _product("Bakery Pricing Calculator", niche="bakery", product_type=ProductType.CALCULATOR)
    cluster_b = _product("Bakery Costing Spreadsheet", niche="bakery", product_type=ProductType.SPREADSHEET)
    run = ProductClusteringService(similarity_threshold=0.4, minimum_cluster_size=2).cluster_products([cluster_a, cluster_b])

    saved_run = repository.save_cluster_run(run.run)
    saved_clusters = [repository.save_cluster(cluster) for cluster in run.clusters]
    saved_memberships = [repository.save_membership(membership) for cluster in run.clusters for membership in cluster.memberships]

    assert saved_run.id is not None
    assert saved_clusters
    assert saved_memberships
    assert repository.list_clusters(limit=10)


def test_cluster_features_expose_resolved_terms_for_auditability():
    product = _product(
        "Custom Cake Pricing Calculator for Home Bakers",
        niche="bakery",
        product_type=ProductType.CALCULATOR,
        keywords=["bakery", "pricing", "calculator"],
        description="Helps home bakers price custom cakes.",
    )

    features = ProductClusterFeatures.from_product(product)
    assert "bakery" in features.niche_terms
    assert "pricing" in features.problem_terms
    assert "calculator" in features.product_type_terms
    assert "custom cake" in " ".join(features.keywords)
