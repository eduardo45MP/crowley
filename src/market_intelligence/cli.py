from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from crawler.config import CrawlerConfig, load_dotenv
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.build_ease.service import BuildEaseAnalysisService
from market_intelligence.competition.service import CompetitionAnalysisService
from market_intelligence.deep_research.service import DeepResearchService
from market_intelligence.demand.service import DemandScoringService
from market_intelligence.differentiation.service import DifferentiationAnalysisService
from market_intelligence.eligibility.service import EligibilityService
from market_intelligence.opportunity.service import OpportunityAnalysisService
from market_intelligence.purchase_intent.service import PurchaseIntentAnalysisService


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
    deep_research_run.add_argument("--verbose", action="store_true")
    deep_research_run.add_argument("--cluster-id", type=int, default=None)
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

    service = OpportunityAnalysisService()
    results = []
    for cluster in clusters:
        inputs = {}
        latest_demand = repository.latest_cluster_demand_score(cluster.id) if cluster.id is not None else None
        latest_competition = repository.latest_cluster_competition_score(cluster.id) if cluster.id is not None else None
        latest_purchase_intent = repository.latest_cluster_purchase_intent_score(cluster.id) if cluster.id is not None else None
        latest_build_ease = repository.latest_cluster_build_ease_score(cluster.id) if cluster.id is not None else None
        latest_differentiation = repository.latest_cluster_differentiation_score(cluster.id) if cluster.id is not None else None
        if latest_demand is not None:
            inputs["demand_score"] = latest_demand.get("demand_score")
            inputs["demand_confidence"] = latest_demand.get("confidence")
            inputs["demand_evidence_coverage"] = latest_demand.get("evidence_coverage")
            inputs["demand_analysis_id"] = latest_demand.get("id")
            inputs["demand_model_version"] = latest_demand.get("model_version")
        if latest_competition is not None:
            inputs["competition_score"] = latest_competition.get("competition_score")
            inputs["competition_confidence"] = latest_competition.get("confidence")
            inputs["competition_evidence_coverage"] = latest_competition.get("evidence_coverage")
            inputs["competition_analysis_id"] = latest_competition.get("id")
            inputs["competition_model_version"] = latest_competition.get("model_version")
        if latest_purchase_intent is not None:
            inputs["purchase_intent_score"] = latest_purchase_intent.get("purchase_intent_score")
            inputs["purchase_intent_confidence"] = latest_purchase_intent.get("confidence")
            inputs["purchase_intent_evidence_coverage"] = latest_purchase_intent.get("evidence_coverage")
            inputs["purchase_intent_analysis_id"] = latest_purchase_intent.get("id")
            inputs["purchase_intent_model_version"] = latest_purchase_intent.get("model_version")
        if latest_build_ease is not None:
            inputs["build_ease_score"] = latest_build_ease.get("build_ease_score")
            inputs["build_ease_confidence"] = latest_build_ease.get("confidence")
            inputs["build_ease_evidence_coverage"] = latest_build_ease.get("evidence_coverage")
            inputs["build_ease_analysis_id"] = latest_build_ease.get("id")
            inputs["build_ease_model_version"] = latest_build_ease.get("model_version")
        if latest_differentiation is not None:
            inputs["differentiation_score"] = latest_differentiation.get("differentiation_score")
            inputs["differentiation_confidence"] = latest_differentiation.get("confidence")
            inputs["differentiation_evidence_coverage"] = latest_differentiation.get("evidence_coverage")
            inputs["differentiation_analysis_id"] = latest_differentiation.get("id")
            inputs["differentiation_model_version"] = latest_differentiation.get("model_version")
        inputs["cluster_id"] = cluster.id
        result = service.analyze_cluster(cluster.id, type("Payload", (), inputs)())
        results.append(result)

    print(f"Clusters analyzed: {len(results)}")
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
        results.append(result)

    print(f"Clusters evaluated: {len(results)}")
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
    print(f"Eligible candidates: {len(normalized_candidates)}")
    print(f"Selected final portfolio: {len(result.selected)}")
    for item in result.selected:
        print(
            f"cluster_id={item.cluster_id} buyer_group={item.buyer_group} score={item.opportunity_score:.2f} "
            f"quota={item.quota_bucket or 'general'}"
        )
    return 0


def _run_deep_research(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    if args.cluster_id is not None:
        cluster = repository.get_cluster_by_id(args.cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
        clusters = [cluster]

    service = DeepResearchService()
    result = service.run(clusters, top=args.top)
    print(f"Deep research dossiers: {len(result.dossiers)}")
    for dossier in result.dossiers:
        print(
            f"cluster_id={dossier.cluster_id} rank={dossier.research_rank} "
            f"coverage={dossier.research_coverage:.2f} confidence={dossier.research_confidence:.2f}"
        )
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
        raise ValueError(f"Comando não suportado: {args.command}")
    except (ValueError, OSError) as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
