from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product, ProductType
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.competition.features import CompetitionFeatureExtractor
from market_intelligence.competition.scoring import CompetitionScorer, competition_density_attractiveness
from market_intelligence.competition.service import CompetitionAnalysisService


def _product(name: str, *, seller: str | None = None, price: Decimal | None = None, review_count: int | None = None, rating: float | None = None, marketplace: Marketplace = Marketplace.MOCK, keywords: list[str] | None = None, description: str | None = None) -> Product:
    return Product(
        product_name=name,
        marketplace=marketplace,
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
        description=description or "Bakery pricing calculator with pricing guidance.",
    )


def _cluster(*members: Product) -> ProductCluster:
    return ProductCluster(
        name="Bakery Pricing Calculators",
        slug="bakery-pricing-calculators",
        niche="bakery",
        product_type="calculator",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
        product_count=len(members),
        confidence=0.8,
        members=list(members),
    )


def test_density_curve_prefers_middle_competitive_counts_over_extremes():
    low = competition_density_attractiveness(1)
    middle = competition_density_attractiveness(20)
    high = competition_density_attractiveness(500)

    assert low < middle
    assert high < middle
    assert 0.0 <= low <= 1.0
    assert 0.0 <= middle <= 1.0
    assert 0.0 <= high <= 1.0


def test_feature_extractor_uses_seller_concentration_and_price_structure():
    members = [
        _product("A", seller="Seller Alpha", price=Decimal("9.99"), review_count=1200, rating=4.7),
        _product("B", seller="Seller Alpha", price=Decimal("10.99"), review_count=1100, rating=4.5),
        _product("C", seller="Seller Beta", price=Decimal("11.99"), review_count=180, rating=4.2),
        _product("D", seller="Seller Gamma", price=Decimal("22.99"), review_count=90, rating=4.1),
        _product("E", seller="Seller Delta", price=Decimal("19.99"), review_count=70, rating=4.0),
    ]

    features = CompetitionFeatureExtractor().extract(_cluster(*members))

    assert features.competitor_count == 5
    assert features.seller_count == 4
    assert features.top_seller_listing_share is not None
    assert features.top_seller_review_share is not None
    assert features.price_median is not None
    assert features.price_mean is not None
    assert features.market_fragmentation is not None
    assert features.price_compression is not None


def test_competition_service_persists_score_and_coverage():
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()

    members = [
        _product("A", seller="Seller Alpha", price=Decimal("9.99"), review_count=200, rating=4.8),
        _product("B", seller="Seller Alpha", price=Decimal("10.99"), review_count=160, rating=4.7),
        _product("C", seller="Seller Beta", price=Decimal("12.99"), review_count=120, rating=4.5),
        _product("D", seller="Seller Gamma", price=Decimal("17.99"), review_count=95, rating=4.2),
        _product("E", seller="Seller Delta", price=Decimal("19.99"), review_count=80, rating=4.1),
    ]
    cluster = repository.save_cluster(_cluster(*members))

    result = CompetitionAnalysisService(repository=repository).analyze_cluster(cluster)

    assert 0.0 <= result.competition_score <= 100.0
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.evidence_coverage <= 1.0
    assert result.id is not None
    assert repository.latest_cluster_competition_score(cluster.id) is not None


def test_competition_scores_distinguish_monopolized_from_fragmented_markets():
    monopolized = _cluster(
        _product("A", seller="Seller Alpha", price=Decimal("8.00"), review_count=9000, rating=4.9),
        _product("B", seller="Seller Alpha", price=Decimal("8.50"), review_count=100, rating=4.8),
        _product("C", seller="Seller Alpha", price=Decimal("9.00"), review_count=50, rating=4.7),
        _product("D", seller="Seller Beta", price=Decimal("11.00"), review_count=25, rating=4.3),
        _product("E", seller="Seller Gamma", price=Decimal("12.00"), review_count=20, rating=4.1),
    )
    fragmented = _cluster(
        _product("A", seller="Seller Alpha", price=Decimal("7.00"), review_count=500, rating=4.2),
        _product("B", seller="Seller Beta", price=Decimal("8.00"), review_count=460, rating=4.1),
        _product("C", seller="Seller Gamma", price=Decimal("9.00"), review_count=440, rating=4.0),
        _product("D", seller="Seller Delta", price=Decimal("12.00"), review_count=420, rating=4.3),
        _product("E", seller="Seller Epsilon", price=Decimal("16.00"), review_count=350, rating=4.4),
    )

    monopolized_score = CompetitionScorer().score(CompetitionFeatureExtractor().extract(monopolized))[0]
    fragmented_score = CompetitionScorer().score(CompetitionFeatureExtractor().extract(fragmented))[0]

    assert fragmented_score > monopolized_score
