from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crawler.clustering import ProductCluster
from crawler.models import Marketplace, Product
from market_intelligence.deep_research.service import DeepResearchService


def _member(name: str, price: str, reviews: int, keywords: list[str] | None = None) -> Product:
    return Product(
        product_name=name,
        marketplace=Marketplace.MOCK,
        url=f"https://example.test/{name.lower().replace(' ', '-')}",
        collected_at=datetime.now(timezone.utc),
        niche="bakery",
        product_type=None,
        price=Decimal(price),
        currency="USD",
        review_count=reviews,
        rating=4.8,
        keywords=keywords or ["bakery", "pricing"],
        description="Bakery pricing spreadsheet for business planning.",
        image_urls=[f"https://example.test/{name.lower().replace(' ', '-')}.png"],
    )


def test_deep_research_creates_deterministic_dossiers_without_mutating_scores():
    cluster = ProductCluster(
        name="Bakery Pricing Templates",
        slug="bakery-pricing-templates",
        niche="bakery",
        product_type="template",
        primary_problem="pricing",
        keywords=["bakery", "pricing", "calculator"],
        product_count=3,
        confidence=0.86,
    )
    cluster.members = [
        _member("Bakery Pricing Sheet", "19.00", 120, ["bakery", "pricing", "sheet"]),
        _member("Recipe Cost Planner", "29.00", 210, ["bakery", "planner", "cost"]),
        _member("Inventory & Pricing Toolkit", "49.00", 330, ["bakery", "inventory", "pricing"]),
    ]

    result = DeepResearchService().run([cluster], top=1)

    assert result.run.target_count == 1
    assert len(result.dossiers) == 1
    dossier = result.dossiers[0]
    assert dossier.cluster_id is None
    assert dossier.cluster_name == "Bakery Pricing Templates"
    assert dossier.status == "completed"
    assert dossier.pricing_analysis["median"] > 0
    assert dossier.market_patterns
    assert dossier.confirmations
    assert dossier.research_coverage >= 0.0
    assert dossier.research_confidence > 0.0
