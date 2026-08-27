from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from crawler.clustering import ClusterRun, ProductCluster, ProductClusterMembership
from crawler.models import Marketplace, Product, RawMarketplaceProduct
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.build_ease.service import BuildEaseAnalysisService
from market_intelligence.competition.service import CompetitionAnalysisService
from market_intelligence.deep_research.service import DeepResearchService
from market_intelligence.demand.service import DemandScoringService
from market_intelligence.differentiation.service import DifferentiationAnalysisService
from market_intelligence.editorial.service import EditorialReportService
from market_intelligence.eligibility.service import EligibilityService
from market_intelligence.opportunity.service import OpportunityAnalysisService
from market_intelligence.product_blueprint.service import ProductBlueprintService
from market_intelligence.purchase_intent.service import PurchaseIntentAnalysisService
from market_intelligence.reporting.exporters import ReportExporter
from market_intelligence.selection.config import SelectionPolicy
from market_intelligence.selection.models import OpportunityCandidate
from market_intelligence.selection.service import PortfolioSelector
from market_intelligence.top10.config import Top10SelectionConfig
from market_intelligence.top10.selection import Top10Selector
from market_intelligence.top10.thesis import OpportunityThesisService


DEMO_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def build_demo_report(repository: SqlAlchemyProductRepository, output_dir: str | Path) -> tuple[object, dict[str, Path]]:
    """Run a deterministic, offline fixture pipeline and publish all report formats."""
    clusters = _persist_demo_observations(repository)
    DemandScoringService(repository=repository).calculate(clusters)
    CompetitionAnalysisService(repository=repository).analyze(clusters)
    PurchaseIntentAnalysisService(repository=repository).analyze(clusters)
    BuildEaseAnalysisService(repository=repository).analyze(clusters)
    DifferentiationAnalysisService(repository=repository).analyze(clusters)
    opportunity = OpportunityAnalysisService(repository=repository).analyze(clusters)

    eligibility_service = EligibilityService()
    eligibility_run = type("EligibilityRun", (), {
        "id": None, "model_version": eligibility_service.model_version,
        "configuration": {"fixture": "deterministic-demo-v1"}, "cluster_count": len(clusters),
        "started_at": DEMO_TIME, "completed_at": DEMO_TIME,
    })()
    repository.save_eligibility_run(eligibility_run)
    eligible_ids: set[int] = set()
    for cluster, analysis in zip(clusters, opportunity.scores, strict=True):
        demand = repository.latest_cluster_demand_score(cluster.id)
        competition = repository.latest_cluster_competition_score(cluster.id)
        differentiation = repository.latest_cluster_differentiation_score(cluster.id)
        build = repository.latest_cluster_build_ease_score(cluster.id)
        result = eligibility_service.evaluate_cluster(
            cluster, analysis,
            demand_score=demand["demand_score"], demand_confidence=demand["confidence"],
            competition_score=competition["competition_score"],
            differentiation_score=differentiation["differentiation_score"],
            differentiation_confidence=differentiation["confidence"],
            evidence_coverage=analysis.evidence_coverage,
            build_ease_score=build["build_ease_score"], estimated_build_hours=8.0,
        )
        result.run_id = eligibility_run.id
        repository.save_cluster_eligibility_result(result)
        if result.ranking_eligible:
            eligible_ids.add(cluster.id)

    candidates = []
    groups = ["small_business", "creators", "ecommerce_sellers", "professional_productivity"]
    for index, cluster in enumerate(clusters):
        if cluster.id not in eligible_ids:
            continue
        score = repository.latest_cluster_opportunity_score(cluster.id)
        candidates.append(OpportunityCandidate(
            cluster_id=cluster.id, cluster_name=cluster.name,
            opportunity_score=score["opportunity_score"], opportunity_confidence=score["opportunity_confidence"],
            evidence_coverage=score["evidence_coverage"], buyer_group=groups[index % len(groups)],
            niche=cluster.niche, problem_type=cluster.primary_problem, product_type=cluster.product_type,
            ranking_eligible=True,
        ))
    if not candidates:
        raise ValueError("A fixture determinística não produziu oportunidades elegíveis; revise as regras de Eligibility.")
    selection = PortfolioSelector(policy=SelectionPolicy(
        target_size=len(candidates), minimum_opportunity_score=0.0, minimum_confidence=0.0,
        minimum_evidence_coverage=0.0, buyer_group_quotas={},
    )).select(candidates)
    repository.save_selection_run(selection.run)
    for item in selection.selected:
        repository.save_selected_opportunity(item, selection.run.id)

    selected_clusters = [repository.get_cluster_by_id(item.cluster_id) for item in selection.selected]
    research = DeepResearchService().run(selected_clusters, top=len(selected_clusters), selection_run_id=selection.run.id)
    repository.save_deep_research_run(research.run)
    for dossier in research.dossiers:
        dossier.run_id = research.run.id
        repository.save_deep_research_dossier(dossier)

    opportunity_scores = {cluster.id: repository.latest_cluster_opportunity_score(cluster.id)["opportunity_score"] for cluster in selected_clusters}
    build_scores = {cluster.id: repository.latest_cluster_build_ease_score(cluster.id)["build_ease_score"] for cluster in selected_clusters}
    top10 = Top10Selector(Top10SelectionConfig(
        target_size=min(10, len(selected_clusters)), minimum_research_coverage=0.0, minimum_research_confidence=0.0,
    )).select(research.dossiers, opportunity_scores=opportunity_scores, build_ease_scores=build_scores)
    top10.run.deep_research_run_id = research.run.id
    repository.save_top10_run(top10.run)
    for item in top10.selected:
        repository.save_top10_opportunity(item, top10.run.id)
        cluster = repository.get_cluster_by_id(item.cluster_id)
        dossier = next(value for value in research.dossiers if value.cluster_id == item.cluster_id)
        thesis = OpportunityThesisService().create(cluster, dossier, item.opportunity_score)
        repository.save_thesis(thesis)
        repository.save_blueprint(ProductBlueprintService().create(cluster, dossier, thesis))

    report = EditorialReportService(repository).build(
        selection_run_id=selection.run.id, top=100, top10_count=10, created_at=DEMO_TIME,
    )
    paths = ReportExporter().export(report, output_dir, ["json", "csv", "xlsx", "pdf"])
    return report, paths


def _persist_demo_observations(repository: SqlAlchemyProductRepository) -> list[ProductCluster]:
    definitions = [
        ("Bakery Pricing Calculator", "bakery", "pricing"),
        ("Creator Sponsorship Rate Calculator", "content creator", "pricing"),
        ("Ecommerce Inventory Margin Tracker", "ecommerce", "inventory"),
        ("Consultant Project Profitability Planner", "consulting", "profitability"),
    ]
    run = ClusterRun(
        algorithm="deterministic_fixture", algorithm_version="demo-v1", similarity_engine="fixture",
        parameters={"source": "offline mock"}, product_count=len(definitions) * 3,
        cluster_count=len(definitions), started_at=DEMO_TIME, completed_at=DEMO_TIME,
    )
    repository.save_cluster_run(run)
    clusters: list[ProductCluster] = []
    for cluster_index, (name, niche, problem) in enumerate(definitions, start=1):
        products: list[Product] = []
        for product_index, price in enumerate(("19.00", "29.00", "49.00"), start=1):
            external_id = f"demo-v1-{cluster_index}-{product_index}"
            raw = repository.save_raw(RawMarketplaceProduct(
                marketplace=Marketplace.MOCK, external_id=external_id, query=name.lower(),
                raw_payload={"name": f"{name} {product_index}", "price": price, "fixture": "demo-v1"},
                collected_at=DEMO_TIME,
            ))
            product = repository.upsert_product(Product(
                product_name=f"{name} {product_index}", marketplace=Marketplace.MOCK,
                url=f"https://example.test/{external_id}", collected_at=DEMO_TIME,
                external_id=external_id, niche=niche, price=Decimal(price), currency="USD",
                review_count=100 * product_index, rating=4.5 + product_index / 10,
                seller=f"demo-seller-{product_index}",
                keywords=[*niche.split(), problem, "calculator", "margin", "workflow"],
                description=f"{name} with cost, labor, margin, dashboard and editable workflow.",
                image_urls=[f"https://example.test/{external_id}.png"], raw_product_id=raw.id,
            )).product
            products.append(product)
        cluster = repository.save_cluster(ProductCluster(
            run_id=run.id, name=name, slug=f"demo-{cluster_index}-{problem}", niche=niche,
            product_type="calculator", primary_problem=problem,
            keywords=[*niche.split(), problem, "calculator", "margin", "workflow"],
            product_count=len(products), confidence=0.9, created_at=DEMO_TIME, updated_at=DEMO_TIME,
        ))
        for product in products:
            repository.save_membership(ProductClusterMembership(
                cluster_id=cluster.id, product=product, membership_score=0.9, created_at=DEMO_TIME,
            ))
        clusters.append(repository.get_cluster_by_id(cluster.id))
    return clusters
