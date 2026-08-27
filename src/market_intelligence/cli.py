from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from crawler.config import CrawlerConfig, load_dotenv
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.build_ease.service import BuildEaseAnalysisService
from market_intelligence.competition.service import CompetitionAnalysisService
from market_intelligence.deep_research.service import DeepResearchService
from market_intelligence.demo import build_demo_report
from market_intelligence.editorial.service import EditorialReportService
from market_intelligence.demand.service import DemandScoringService
from market_intelligence.differentiation.service import DifferentiationAnalysisService
from market_intelligence.eligibility.service import EligibilityService
from market_intelligence.opportunity.service import OpportunityAnalysisService
from market_intelligence.product_blueprint.service import ProductBlueprintService
from market_intelligence.purchase_intent.service import PurchaseIntentAnalysisService
from market_intelligence.reporting.exporters import ReportExporter
from market_intelligence.top10.selection import Top10Selector
from market_intelligence.top10.thesis import OpportunityThesisService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-intelligence", description="Market intelligence over product clusters")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demand = subparsers.add_parser("demand", help="score demand for product clusters")
    demand_subparsers = demand.add_subparsers(dest="demand_command", required=True)
    demand_calculate = demand_subparsers.add_parser("calculate", help="calculate demand scores for clusters in the database")
    demand_calculate.add_argument("--limit", type=int, default=50)
    demand_calculate.add_argument("--verbose", action="store_true")
    demand_calculate.add_argument("--cluster-id", type=int, default=None)

    competition = subparsers.add_parser("competition", help="score competitive environment for product clusters")
    competition_subparsers = competition.add_subparsers(dest="competition_command", required=True)
    competition_calculate = competition_subparsers.add_parser("calculate", help="calculate competition scores for clusters in the database")
    competition_calculate.add_argument("--limit", type=int, default=50)
    competition_calculate.add_argument("--verbose", action="store_true")
    competition_calculate.add_argument("--cluster-id", type=int, default=None)

    purchase_intent = subparsers.add_parser("purchase-intent", help="score purchase intent for product clusters")
    purchase_intent_subparsers = purchase_intent.add_subparsers(dest="purchase_intent_command", required=True)
    purchase_intent_calculate = purchase_intent_subparsers.add_parser("calculate", help="calculate purchase-intent scores for clusters in the database")
    purchase_intent_calculate.add_argument("--limit", type=int, default=50)
    purchase_intent_calculate.add_argument("--verbose", action="store_true")
    purchase_intent_calculate.add_argument("--cluster-id", type=int, default=None)

    build_ease = subparsers.add_parser("build-ease", help="score ease of production for product clusters")
    build_ease_subparsers = build_ease.add_subparsers(dest="build_ease_command", required=True)
    build_ease_calculate = build_ease_subparsers.add_parser("calculate", help="calculate build-ease scores for clusters in the database")
    build_ease_calculate.add_argument("--limit", type=int, default=50)
    build_ease_calculate.add_argument("--verbose", action="store_true")
    build_ease_calculate.add_argument("--cluster-id", type=int, default=None)

    differentiation = subparsers.add_parser("differentiation", help="score differentiation potential for product clusters")
    differentiation_subparsers = differentiation.add_subparsers(dest="differentiation_command", required=True)
    differentiation_calculate = differentiation_subparsers.add_parser("calculate", help="calculate differentiation scores for clusters in the database")
    differentiation_calculate.add_argument("--limit", type=int, default=50)
    differentiation_calculate.add_argument("--verbose", action="store_true")
    differentiation_calculate.add_argument("--cluster-id", type=int, default=None)

    opportunity = subparsers.add_parser("opportunity", help="aggregate independent market-intelligence dimensions into an opportunity score")
    opportunity_subparsers = opportunity.add_subparsers(dest="opportunity_command", required=True)
    opportunity_calculate = opportunity_subparsers.add_parser("calculate", help="calculate opportunity scores for clusters in the database")
    opportunity_calculate.add_argument("--limit", type=int, default=50)
    opportunity_calculate.add_argument("--verbose", action="store_true")
    opportunity_calculate.add_argument("--cluster-id", type=int, default=None)

    eligibility = subparsers.add_parser("eligibility", help="evaluate ranking eligibility for opportunities")
    eligibility_subparsers = eligibility.add_subparsers(dest="eligibility_command", required=True)
    eligibility_evaluate = eligibility_subparsers.add_parser("evaluate", help="evaluate eligibility for clusters in the database")
    eligibility_evaluate.add_argument("--limit", type=int, default=50)
    eligibility_evaluate.add_argument("--verbose", action="store_true")
    eligibility_evaluate.add_argument("--cluster-id", type=int, default=None)

    selection = subparsers.add_parser("selection", help="select the final portfolio from eligible opportunities")
    selection_subparsers = selection.add_subparsers(dest="selection_command", required=True)
    selection_run = selection_subparsers.add_parser("run", help="run portfolio selection for eligible clusters")
    selection_run.add_argument("--limit", type=int, default=200)
    selection_run.add_argument("--verbose", action="store_true")
    selection_run.add_argument("--cluster-id", type=int, default=None)

    deep_research = subparsers.add_parser("deep-research", help="run evidence-based due diligence for selected opportunities")
    deep_research_subparsers = deep_research.add_subparsers(dest="deep_research_command", required=True)
    deep_research_run = deep_research_subparsers.add_parser("run", help="run deep research for shortlisted clusters")
    deep_research_run.add_argument("--limit", type=int, default=25)
    deep_research_run.add_argument("--top", type=int, default=25)
    deep_research_run.add_argument("--selection-run", type=int, default=None)
    deep_research_run.add_argument("--verbose", action="store_true")
    deep_research_run.add_argument("--cluster-id", type=int, default=None)

    deep_research_show = deep_research_subparsers.add_parser("show", help="show a deep research dossier for a cluster")
    deep_research_show.add_argument("--cluster-id", type=int, default=None)
    deep_research_show.add_argument("--top", type=int, default=1)
    deep_research_show.add_argument("--verbose", action="store_true")

    deep_research_export = deep_research_subparsers.add_parser("export", help="export deep research dossiers to JSON/CSV summary")
    deep_research_export.add_argument("--selection-run", type=int, default=None)
    deep_research_export.add_argument("--top", type=int, default=25)
    deep_research_export.add_argument("--output-dir", type=str, default="data/research")
    deep_research_export.add_argument("--verbose", action="store_true")

    top10 = subparsers.add_parser("top10", help="select the final top 10 opportunities from deep research dossiers")
    top10_subparsers = top10.add_subparsers(dest="top10_command", required=True)
    top10_select = top10_subparsers.add_parser("select", help="select the final top 10 from the most recent deep research dossiers")
    top10_select.add_argument("--limit", type=int, default=25)
    top10_select.add_argument("--top", type=int, default=10)
    top10_select.add_argument("--selection-run", type=int, default=None)
    top10_select.add_argument("--verbose", action="store_true")
    top10_select.add_argument("--cluster-id", type=int, default=None)

    top10_show = top10_subparsers.add_parser("show", help="show a selected top 10 opportunity and its evidence")
    top10_show.add_argument("--cluster-id", type=int, default=None)
    top10_show.add_argument("--limit", type=int, default=25)
    top10_show.add_argument("--top", type=int, default=10)
    top10_show.add_argument("--verbose", action="store_true")

    top10_export = top10_subparsers.add_parser("export", help="export the top 10 selection summary")
    top10_export.add_argument("--selection-run", type=int, default=None)
    top10_export.add_argument("--top", type=int, default=10)
    top10_export.add_argument("--output-dir", type=str, default="data/top10")
    top10_export.add_argument("--verbose", action="store_true")

    thesis = subparsers.add_parser("thesis", help="show the opportunity thesis derived from deep research evidence")
    thesis_subparsers = thesis.add_subparsers(dest="thesis_command", required=True)
    thesis_show = thesis_subparsers.add_parser("show", help="show an opportunity thesis for a cluster")
    thesis_show.add_argument("--cluster-id", type=int, default=None)
    thesis_show.add_argument("--limit", type=int, default=25)
    thesis_show.add_argument("--verbose", action="store_true")

    blueprint = subparsers.add_parser("blueprint", help="generate product blueprints for selected top 10 opportunities")
    blueprint_subparsers = blueprint.add_subparsers(dest="blueprint_command", required=True)
    blueprint_generate = blueprint_subparsers.add_parser("generate", help="generate product blueprints from the selected top 10")
    blueprint_generate.add_argument("--top", type=int, default=10)
    blueprint_generate.add_argument("--limit", type=int, default=25)
    blueprint_generate.add_argument("--selection-run", type=int, default=None)
    blueprint_generate.add_argument("--verbose", action="store_true")
    blueprint_generate.add_argument("--cluster-id", type=int, default=None)

    blueprint_show = blueprint_subparsers.add_parser("show", help="show a generated product blueprint for a cluster")
    blueprint_show.add_argument("--cluster-id", type=int, default=None)
    blueprint_show.add_argument("--top", type=int, default=10)
    blueprint_show.add_argument("--verbose", action="store_true")

    report = subparsers.add_parser("report", help="build and inspect immutable editorial report snapshots")
    report_subparsers = report.add_subparsers(dest="report_command", required=True)
    report_build = report_subparsers.add_parser("build", help="build canonical JSON and complementary report artifacts")
    report_build.add_argument("--selection-run", type=int, default=None)
    report_build.add_argument("--top", type=int, default=100)
    report_build.add_argument("--top10", type=int, default=10)
    report_build.add_argument("--output-dir", type=str, default="data/reports")
    report_build.add_argument("--formats", type=str, default="json,csv,xlsx,pdf")
    report_build.add_argument("--verbose", action="store_true")
    report_show = report_subparsers.add_parser("show", help="show metadata for an existing report snapshot")
    report_show.add_argument("--report-id", type=str, default=None)
    report_show.add_argument("--output-dir", type=str, default="data/reports")
    report_show.add_argument("--verbose", action="store_true")

    pipeline = subparsers.add_parser("pipeline", help="run deterministic offline pipeline fixtures")
    pipeline_subparsers = pipeline.add_subparsers(dest="pipeline_command", required=True)
    pipeline_demo = pipeline_subparsers.add_parser("demo", help="run the complete offline mock pipeline and build a report")
    pipeline_demo.add_argument("--output-dir", type=str, default="data/reports")
    pipeline_demo.add_argument("--verbose", action="store_true")
    return parser


def _repository(config: CrawlerConfig) -> SqlAlchemyProductRepository:
    repository = SqlAlchemyProductRepository(config.database_url)
    repository.create_schema()
    return repository


def _run_demand_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    result = DemandScoringService(repository=repository).calculate(clusters)
    print(f"Clusters analyzed: {len(result.scores)}")
    print(f"Run ID: {result.run.id}")
    for score in sorted(result.scores, key=lambda item: (-item.demand_score, item.cluster_id or 0)):
        print(f"cluster_id={score.cluster_id} demand={score.demand_score:.2f} confidence={score.confidence:.2f} coverage={score.evidence_coverage:.2f}")
    return 0


def _run_competition_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    result = CompetitionAnalysisService(repository=repository).analyze(clusters)
    print(f"Clusters analyzed: {len(result.scores)}")
    print(f"Run ID: {result.run.id}")
    for score in sorted(result.scores, key=lambda item: (-item.competition_score, item.cluster_id or 0)):
        print(f"cluster_id={score.cluster_id} competition={score.competition_score:.2f} confidence={score.confidence:.2f} coverage={score.evidence_coverage:.2f}")
    return 0


def _run_purchase_intent_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    result = PurchaseIntentAnalysisService(repository=repository).analyze(clusters)
    print(f"Clusters analyzed: {len(result.scores)}")
    print(f"Run ID: {result.run.id}")
    for score in sorted(result.scores, key=lambda item: (-item.purchase_intent_score, item.cluster_id or 0)):
        print(f"cluster_id={score.cluster_id} purchase_intent={score.purchase_intent_score:.2f} confidence={score.confidence:.2f} coverage={score.evidence_coverage:.2f}")
    return 0


def _run_build_ease_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    result = BuildEaseAnalysisService(repository=repository).analyze(clusters)
    print(f"Clusters analyzed: {len(result.scores)}")
    print(f"Run ID: {result.run.id}")
    for score in sorted(result.scores, key=lambda item: (-item.build_ease_score, item.cluster_id or 0)):
        print(f"cluster_id={score.cluster_id} build_ease={score.build_ease_score:.2f} confidence={score.confidence:.2f} coverage={score.evidence_coverage:.2f}")
    return 0


def _run_differentiation_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    result = DifferentiationAnalysisService(repository=repository).analyze(clusters)
    print(f"Clusters analyzed: {len(result.scores)}")
    print(f"Run ID: {result.run.id}")
    for score in sorted(result.scores, key=lambda item: (-item.differentiation_score, item.cluster_id or 0)):
        print(f"cluster_id={score.cluster_id} differentiation={score.differentiation_score:.2f} confidence={score.confidence:.2f} coverage={score.evidence_coverage:.2f}")
    return 0


def _run_opportunity_calculate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    analysis = OpportunityAnalysisService(repository=repository).analyze(clusters)
    results = analysis.scores

    print(f"Clusters analyzed: {len(results)}")
    print(f"Run ID: {analysis.run.id}")
    for result in sorted(results, key=lambda item: (-(item.opportunity_score or 0.0), item.cluster_id or 0)):
        print(f"cluster_id={result.cluster_id} opportunity={result.opportunity_score if result.opportunity_score is not None else 'n/a'} status={result.status} qualification={result.qualification}")
    return 0


def _run_eligibility_evaluate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    service = EligibilityService()
    now = datetime.now(timezone.utc)
    run = type("EligibilityRun", (), {"id": None, "model_version": service.model_version, "configuration": {"policy": "default"}, "cluster_count": len(clusters), "started_at": now, "completed_at": now})()
    repository.save_eligibility_run(run)
    results = []
    for cluster in clusters:
        opportunity = None
        latest_opportunity = repository.latest_cluster_opportunity_score(cluster.id) if cluster.id is not None else None
        if latest_opportunity is not None:
            opportunity = type(
                "OpportunitySnapshot",
                (),
                {
                    "cluster_id": cluster.id,
                    "opportunity_score": latest_opportunity.get("opportunity_score"),
                    "status": latest_opportunity.get("status"),
                    "qualification": latest_opportunity.get("qualification"),
                    "opportunity_confidence": latest_opportunity.get("opportunity_confidence"),
                    "evidence_coverage": latest_opportunity.get("evidence_coverage"),
                    "components": latest_opportunity.get("components") or {},
                    "source_analysis_ids": latest_opportunity.get("source_analysis_ids") or {},
                    "warnings": latest_opportunity.get("warnings") or [],
                },
            )()

        dominant_demand = repository.latest_cluster_demand_score(cluster.id) if cluster.id is not None else None
        demand_score = dominant_demand.get("demand_score") if dominant_demand is not None else None
        demand_confidence = dominant_demand.get("confidence") if dominant_demand is not None else None
        competition = repository.latest_cluster_competition_score(cluster.id) if cluster.id is not None else None
        differentiation = repository.latest_cluster_differentiation_score(cluster.id) if cluster.id is not None else None
        result = service.evaluate_cluster(
            cluster,
            opportunity=opportunity,
            demand_score=demand_score,
            demand_confidence=demand_confidence,
            competition_score=competition.get("competition_score") if competition is not None else None,
            differentiation_score=differentiation.get("differentiation_score") if differentiation is not None else None,
            differentiation_confidence=differentiation.get("confidence") if differentiation is not None else None,
            evidence_coverage=opportunity.evidence_coverage if opportunity is not None else None,
        )
        result.run_id = run.id
        repository.save_cluster_eligibility_result(result)
        results.append(result)

    print(f"Clusters evaluated: {len(results)}")
    print(f"Run ID: {run.id}")
    counts = {"eligible": 0, "ineligible": 0, "review_required": 0, "insufficient_data": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    print(f"Eligible: {counts['eligible']} | Review required: {counts['review_required']} | Ineligible: {counts['ineligible']} | Insufficient data: {counts['insufficient_data']}")
    return 0


def _build_buyer_group(cluster: object) -> str:
    niche = (getattr(cluster, "niche", None) or "").lower()
    if any(key in niche for key in ["bakery", "food", "cafe", "restaurant", "retail"]):
        return "small_business"
    if any(key in niche for key in ["creator", "content", "influencer", "social", "youtube", "podcast"]):
        return "creators"
    if any(key in niche for key in ["legal", "consult", "clinic", "health", "medical", "professional"]):
        return "independent_professionals"
    if any(key in niche for key in ["hotel", "property", "vacation", "rental", "hospitality"]):
        return "property_hospitality"
    if any(key in niche for key in ["shopify", "ecommerce", "store", "inventory", "commerce"]):
        return "ecommerce_sellers"
    if any(key in niche for key in ["hobby", "craft", "maker", "side", "creator"]):
        return "monetized_hobbies"
    if any(key in niche for key in ["productivity", "workflow", "ops", "scheduler", "admin"]):
        return "professional_productivity"
    return "other"


def _run_selection_run(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    candidates = []
    for cluster in clusters:
        if cluster.id is None:
            continue
        latest_opportunity = repository.latest_cluster_opportunity_score(cluster.id)
        latest_eligibility = repository.latest_cluster_eligibility_result(cluster.id)
        if latest_opportunity is None or latest_eligibility is None:
            continue
        if not latest_eligibility.get("ranking_eligible", False):
            continue
        candidate = type(
            "CandidateSnapshot",
            (),
            {
                "cluster_id": cluster.id,
                "cluster_name": cluster.name,
                "opportunity_score": latest_opportunity.get("opportunity_score"),
                "opportunity_confidence": latest_opportunity.get("opportunity_confidence"),
                "evidence_coverage": latest_opportunity.get("evidence_coverage"),
                "buyer_group": _build_buyer_group(cluster),
                "niche": cluster.niche,
                "problem_type": cluster.primary_problem,
                "product_type": cluster.product_type,
                "demand_score": None,
                "competition_score": None,
                "purchase_intent_score": None,
                "build_ease_score": None,
                "differentiation_score": None,
                "price_potential_score": None,
                "ranking_eligible": bool(latest_eligibility.get("ranking_eligible", False)),
            },
        )()
        candidates.append(candidate)

    from market_intelligence.selection.models import OpportunityCandidate
    normalized_candidates = [
        OpportunityCandidate(
            cluster_id=getattr(candidate, "cluster_id", None),
            cluster_name=getattr(candidate, "cluster_name", None),
            opportunity_score=getattr(candidate, "opportunity_score", None),
            opportunity_confidence=getattr(candidate, "opportunity_confidence", None),
            evidence_coverage=getattr(candidate, "evidence_coverage", None),
            buyer_group=getattr(candidate, "buyer_group", None),
            niche=getattr(candidate, "niche", None),
            problem_type=getattr(candidate, "problem_type", None),
            product_type=getattr(candidate, "product_type", None),
            demand_score=getattr(candidate, "demand_score", None),
            competition_score=getattr(candidate, "competition_score", None),
            purchase_intent_score=getattr(candidate, "purchase_intent_score", None),
            build_ease_score=getattr(candidate, "build_ease_score", None),
            differentiation_score=getattr(candidate, "differentiation_score", None),
            price_potential_score=getattr(candidate, "price_potential_score", None),
            ranking_eligible=getattr(candidate, "ranking_eligible", True),
        )
        for candidate in candidates
    ]

    result = __import__("market_intelligence.selection.service", fromlist=["PortfolioSelector"]).PortfolioSelector().select(normalized_candidates)
    repository.save_selection_run(result.run)
    for item in result.selected:
        repository.save_selected_opportunity(item, result.run.id)
    print(f"Eligible candidates: {len(normalized_candidates)}")
    print(f"Selected final portfolio: {len(result.selected)}")
    print(f"Run ID: {result.run.id}")
    for item in result.selected:
        print(
            f"cluster_id={item.cluster_id} buyer_group={item.buyer_group} score={item.opportunity_score:.2f} "
            f"quota={item.quota_bucket or 'general'}"
        )
    return 0


def _run_deep_research(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    selection_run_id = getattr(args, "selection_run", None)
    clusters = _load_candidate_clusters(repository, limit=args.limit, cluster_id=None, selection_run_id=selection_run_id)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    service = DeepResearchService()
    result = service.run(clusters, top=args.top, selection_run_id=selection_run_id)
    repository.save_deep_research_run(result.run)
    for dossier in result.dossiers:
        dossier.run_id = result.run.id
        repository.save_deep_research_dossier(dossier)
    print(f"Deep research dossiers: {len(result.dossiers)}")
    print(f"Run ID: {result.run.id}")
    for dossier in result.dossiers:
        print(
            f"cluster_id={dossier.cluster_id} rank={dossier.research_rank} "
            f"coverage={dossier.research_coverage:.2f} confidence={dossier.research_confidence:.2f}"
        )
    return 0


def _run_deep_research_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    cluster = None
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
    else:
        clusters = repository.list_clusters(limit=max(1, args.top))
        cluster = clusters[0] if clusters else None
    if cluster is None:
        raise ValueError("Nenhum cluster disponível para deep research.")

    dossier = DeepResearchService().research_cluster(cluster)
    print(f"{dossier.cluster_name or cluster.name}")
    print(f"Opportunity Score: {getattr(cluster, 'confidence', 0.0) or 0.0:.2f}")
    print(f"Research Coverage: {dossier.research_coverage:.2f}")
    print(f"Research Confidence: {dossier.research_confidence:.2f}")
    print(f"Competitors analyzed: {dossier.competitor_count_analyzed}")
    if dossier.pricing_analysis.get("median") is not None:
        print(f"Price median: ${dossier.pricing_analysis['median']:.2f}")
    if dossier.observed_gaps:
        print("Leading gaps:")
        for index, gap in enumerate(dossier.observed_gaps[:3], start=1):
            print(f"{index}. {gap}")
    if dossier.warnings:
        print("Warnings:")
        for warning in dossier.warnings:
            print(f"- {warning}")
    return 0


def _run_deep_research_export(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.top), selection_run_id=args.selection_run)
    result = DeepResearchService().run(clusters, top=args.top, selection_run_id=args.selection_run)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    export_json = output_dir / "deep_research.json"
    payload = [dossier.as_dict() for dossier in result.dossiers]
    export_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    csv_path = output_dir / "deep_research_summary.csv"
    csv_lines = ["cluster_id,cluster_name,coverage,confidence,status"]
    for dossier in result.dossiers:
        csv_lines.append(f"{dossier.cluster_id},{dossier.cluster_name},{dossier.research_coverage:.2f},{dossier.research_confidence:.2f},{dossier.status}")
    csv_path.write_text("\n".join(csv_lines), encoding="utf-8")
    print(f"Exported {len(result.dossiers)} dossiers to {output_dir}")
    return 0


def _load_candidate_clusters(
    repository: SqlAlchemyProductRepository,
    limit: int = 25,
    cluster_id: int | None = None,
    selection_run_id: int | None = None,
):
    if selection_run_id is not None:
        run = repository.get_selection_run(selection_run_id)
        if run is None:
            raise ValueError(f"Selection run {selection_run_id} não encontrado.")
        rows = repository.list_selected_opportunities(selection_run_id, limit=limit)
        clusters = [repository.get_cluster_by_id(int(row["cluster_id"])) for row in rows]
        clusters = [cluster for cluster in clusters if cluster is not None]
        if not clusters:
            raise ValueError(f"Selection run {selection_run_id} não possui oportunidades persistidas.")
    else:
        clusters = repository.list_clusters(limit=limit)
    if cluster_id is not None:
        cluster = repository.get_cluster_by_id(cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {cluster_id} não encontrado.")
        clusters = [cluster]
    return clusters


def _opportunity_score_lookup(repository: SqlAlchemyProductRepository, clusters: list) -> dict[int | None, float]:
    scores: dict[int | None, float] = {}
    for cluster in clusters:
        if cluster.id is None:
            continue
        latest = repository.latest_cluster_opportunity_score(cluster.id)
        if latest is not None and latest.get("opportunity_score") is not None:
            scores[cluster.id] = float(latest["opportunity_score"])
    return scores


def _build_ease_lookup(repository: SqlAlchemyProductRepository, clusters: list) -> dict[int | None, float]:
    scores: dict[int | None, float] = {}
    for cluster in clusters:
        if cluster.id is None:
            continue
        latest = repository.latest_cluster_build_ease_score(cluster.id)
        if latest is not None and latest.get("build_ease_score") is not None:
            scores[cluster.id] = float(latest["build_ease_score"])
    return scores


def _run_top10_select(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.limit), cluster_id=getattr(args, "cluster_id", None), selection_run_id=getattr(args, "selection_run", None))
    research = DeepResearchService().run(clusters, top=max(1, args.top), selection_run_id=getattr(args, "selection_run", None))
    selection = Top10Selector().select(
        research.dossiers,
        opportunity_scores=_opportunity_score_lookup(repository, clusters),
        build_ease_scores=_build_ease_lookup(repository, clusters),
    )
    repository.save_deep_research_run(research.run)
    for dossier in research.dossiers:
        dossier.run_id = research.run.id
        repository.save_deep_research_dossier(dossier)
    selection.run.deep_research_run_id = research.run.id
    repository.save_top10_run(selection.run)
    for item in selection.selected:
        repository.save_top10_opportunity(item, selection.run.id)
    print(f"Candidates: {len(research.dossiers)}")
    print(f"Selected: {len(selection.selected)}")
    print(f"Run ID: {selection.run.id}")
    for item in selection.selected:
        print(f"{item.top10_rank}. {item.cluster_name or item.cluster_id} | Opportunity: {item.opportunity_score:.2f} | Research Confidence: {item.research_confidence:.2f} | Selection Utility: {item.top10_selection_utility:.2f}")
    return 0


def _run_top10_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.limit), cluster_id=getattr(args, "cluster_id", None))
    research = DeepResearchService().run(clusters, top=max(1, args.top), selection_run_id=None)
    selection = Top10Selector().select(
        research.dossiers,
        opportunity_scores=_opportunity_score_lookup(repository, clusters),
        build_ease_scores=_build_ease_lookup(repository, clusters),
    )
    target = None
    if args.cluster_id is not None:
        target = next((item for item in selection.selected if item.cluster_id == args.cluster_id), None)
    else:
        target = selection.selected[0] if selection.selected else None
    if target is None:
        raise ValueError("Nenhuma oportunidade no Top 10 disponível para exibir.")
    dossier = next((d for d in research.dossiers if d.cluster_id == target.cluster_id), None)
    if dossier is None:
        raise ValueError(f"Dossier para cluster {target.cluster_id} não encontrado.")
    print(f"{target.cluster_name or 'Top 10 Opportunity'}")
    print(f"Opportunity Score: {target.opportunity_score:.2f}")
    print(f"Research Confidence: {target.research_confidence:.2f}")
    print(f"Selection Utility: {target.top10_selection_utility:.2f}")
    print(f"Verdict: {target.deep_research_verdict}")
    print("Reasons:")
    for reason in target.selection_reasons:
        print(f"- {reason}")
    if dossier.observed_gaps:
        print("Observed gaps:")
        for gap in dossier.observed_gaps[:5]:
            print(f"- {gap}")
    return 0


def _run_top10_export(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.top), cluster_id=None, selection_run_id=args.selection_run)
    research = DeepResearchService().run(clusters, top=max(1, args.top), selection_run_id=args.selection_run)
    selection = Top10Selector().select(
        research.dossiers,
        opportunity_scores=_opportunity_score_lookup(repository, clusters),
        build_ease_scores=_build_ease_lookup(repository, clusters),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    export_json = output_dir / "top10_selection.json"
    payload = [item.as_dict() for item in selection.selected]
    export_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    csv_path = output_dir / "top10_selection_summary.csv"
    lines = ["rank,cluster_id,cluster_name,opportunity_score,selection_utility,research_confidence,verdict"]
    for item in selection.selected:
        lines.append(f"{item.top10_rank},{item.cluster_id},{item.cluster_name},{item.opportunity_score:.2f},{item.top10_selection_utility:.2f},{item.research_confidence:.2f},{item.deep_research_verdict}")
    csv_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(selection.selected)} top 10 items to {output_dir}")
    return 0


def _run_thesis_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.limit), cluster_id=getattr(args, "cluster_id", None))
    cluster = clusters[0] if clusters else None
    if cluster is None:
        raise ValueError("Nenhum cluster disponível para gerar tese.")
    dossier = DeepResearchService().research_cluster(cluster)
    thesis = OpportunityThesisService().create(cluster, dossier, opportunity_score=repository.latest_cluster_opportunity_score(cluster.id).get("opportunity_score") if repository.latest_cluster_opportunity_score(cluster.id) else None)
    repository.save_thesis(thesis)
    print(f"{cluster.name}")
    print(f"Target Buyer: {thesis.target_buyer}")
    print(f"Problem: {thesis.problem}")
    print("Market evidence:")
    for item in thesis.market_evidence:
        print(f"- {item}")
    print("Critical gaps:")
    for item in thesis.critical_gaps:
        print(f"- {item}")
    print(f"Opportunity statement: {thesis.opportunity_statement}")
    return 0


def _run_blueprint_generate(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = _load_candidate_clusters(repository, limit=max(1, args.limit), cluster_id=getattr(args, "cluster_id", None), selection_run_id=getattr(args, "selection_run", None))
    research = DeepResearchService().run(clusters, top=max(1, args.top), selection_run_id=getattr(args, "selection_run", None))
    selection = Top10Selector().select(
        research.dossiers,
        opportunity_scores=_opportunity_score_lookup(repository, clusters),
        build_ease_scores=_build_ease_lookup(repository, clusters),
    )
    blueprints = []
    service = ProductBlueprintService()
    for item in selection.selected:
        cluster = repository.get_cluster_by_id(item.cluster_id) if item.cluster_id is not None else None
        dossier = next((d for d in research.dossiers if d.cluster_id == item.cluster_id), None)
        if cluster is None or dossier is None:
            continue
        thesis = OpportunityThesisService().create(cluster, dossier, opportunity_score=item.opportunity_score)
        repository.save_thesis(thesis)
        blueprint = service.create(cluster, dossier, thesis)
        repository.save_blueprint(blueprint)
        blueprints.append(blueprint)
    print(f"Generated {len(blueprints)} blueprints")
    for blueprint in blueprints:
        print(f"- {blueprint.product_name} | Scope: {blueprint.scope_level} | Hours: {blueprint.estimated_build_hours}")
    return 0


def _run_blueprint_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    cluster = repository.get_cluster_by_id(args.cluster_id) if args.cluster_id is not None else None
    if cluster is None:
        raise ValueError("Nenhum cluster disponível para exibir blueprint.")
    dossier = DeepResearchService().research_cluster(cluster)
    thesis = OpportunityThesisService().create(cluster, dossier, opportunity_score=repository.latest_cluster_opportunity_score(cluster.id).get("opportunity_score") if repository.latest_cluster_opportunity_score(cluster.id) else None)
    blueprint = ProductBlueprintService().create(cluster, dossier, thesis)
    print(f"{blueprint.product_name}")
    print(f"Target: {blueprint.target_buyer}")
    print(f"Primary problem: {blueprint.primary_problem}")
    print("MVP features:")
    for feature in blueprint.mvp_features:
        print(f"- {feature}")
    print("Differentiators:")
    for feature in blueprint.differentiation_features:
        print(f"- {feature}")
    print(f"Estimated build: {blueprint.estimated_build_hours}h")
    return 0


def _run_report_build(args: argparse.Namespace, config: CrawlerConfig) -> int:
    if args.top < 1 or args.top > 100:
        raise ValueError("--top deve estar entre 1 e 100.")
    if args.top10 < 1 or args.top10 > 10:
        raise ValueError("--top10 deve estar entre 1 e 10.")
    repository = _repository(config)
    report = EditorialReportService(repository).build(
        selection_run_id=args.selection_run,
        top=args.top,
        top10_count=args.top10,
    )
    formats = [item for item in args.formats.split(",") if item.strip()]
    paths = ReportExporter().export(report, args.output_dir, formats)
    print(f"Report ID: {report.snapshot.report_id}")
    print(f"Selection Run ID: {report.snapshot.selection_run_id}")
    print(f"Deep Research Run ID: {report.snapshot.deep_research_run_id or 'n/a'}")
    print(f"Opportunities: {len(report.ranking)} | Top 10: {len(report.top10)}")
    for format_name, path in paths.items():
        print(f"{format_name.upper()}: {path}")
    return 0


def _run_report_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    root = Path(args.output_dir)
    if args.report_id:
        path = root / args.report_id / "report.json"
    else:
        candidates = sorted(root.glob("*/report.json")) if root.exists() else []
        path = candidates[-1] if candidates else root / "missing" / "report.json"
    if not path.exists():
        raise ValueError(f"Nenhum report.json encontrado em {root}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata") or {}
    summary = payload.get("summary") or {}
    print(f"Report ID: {metadata.get('report_id')}")
    print(f"Created at: {metadata.get('created_at')}")
    print(f"Selection Run ID: {metadata.get('selection_run_id')}")
    print(f"Opportunities: {summary.get('opportunity_count')} | Top 10: {summary.get('top10_count')}")
    print(f"Path: {path}")
    return 0


def _run_pipeline_demo(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    report, paths = build_demo_report(repository, args.output_dir)
    print(f"Report ID: {report.snapshot.report_id}")
    print(f"Opportunities: {len(report.ranking)} | Top 10: {len(report.top10)}")
    for format_name, path in paths.items():
        print(f"{format_name.upper()}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    load_dotenv(Path(".env"))
    config = CrawlerConfig.from_env()
    try:
        if args.command == "demand" and args.demand_command == "calculate":
            return _run_demand_calculate(args, config)
        if args.command == "competition" and args.competition_command == "calculate":
            return _run_competition_calculate(args, config)
        if args.command == "purchase-intent" and args.purchase_intent_command == "calculate":
            return _run_purchase_intent_calculate(args, config)
        if args.command == "build-ease" and args.build_ease_command == "calculate":
            return _run_build_ease_calculate(args, config)
        if args.command == "differentiation" and args.differentiation_command == "calculate":
            return _run_differentiation_calculate(args, config)
        if args.command == "opportunity" and args.opportunity_command == "calculate":
            return _run_opportunity_calculate(args, config)
        if args.command == "eligibility" and args.eligibility_command == "evaluate":
            return _run_eligibility_evaluate(args, config)
        if args.command == "selection" and args.selection_command == "run":
            return _run_selection_run(args, config)
        if args.command == "deep-research" and args.deep_research_command == "run":
            return _run_deep_research(args, config)
        if args.command == "deep-research" and args.deep_research_command == "show":
            return _run_deep_research_show(args, config)
        if args.command == "deep-research" and args.deep_research_command == "export":
            return _run_deep_research_export(args, config)
        if args.command == "top10" and args.top10_command == "select":
            return _run_top10_select(args, config)
        if args.command == "top10" and args.top10_command == "show":
            return _run_top10_show(args, config)
        if args.command == "top10" and args.top10_command == "export":
            return _run_top10_export(args, config)
        if args.command == "thesis" and args.thesis_command == "show":
            return _run_thesis_show(args, config)
        if args.command == "blueprint" and args.blueprint_command == "generate":
            return _run_blueprint_generate(args, config)
        if args.command == "blueprint" and args.blueprint_command == "show":
            return _run_blueprint_show(args, config)
        if args.command == "report" and args.report_command == "build":
            return _run_report_build(args, config)
        if args.command == "report" and args.report_command == "show":
            return _run_report_show(args, config)
        if args.command == "pipeline" and args.pipeline_command == "demo":
            return _run_pipeline_demo(args, config)
        raise ValueError(f"Comando não suportado: {args.command}")
    except (ValueError, OSError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
