from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.opportunity.config import OpportunityScoreConfig
from market_intelligence.opportunity.models import OpportunityAnalysis, OpportunityInputs, OpportunityScoreResult
from market_intelligence.opportunity.scoring import OpportunityScorer


@dataclass(slots=True)
class OpportunityAnalysisResult:
    run: object
    scores: list[OpportunityAnalysis]


@dataclass(slots=True)
class OpportunityAnalysisService:
    repository: SqlAlchemyProductRepository | None = None
    config: OpportunityScoreConfig | None = None
    scorer: OpportunityScorer | None = None
    model_version: str = "opportunity-v1"

    def __post_init__(self) -> None:
        self.config = self.config or OpportunityScoreConfig()
        self.scorer = self.scorer or OpportunityScorer(self.config)

    def analyze_cluster(self, cluster_id: int | None, inputs: OpportunityInputs | None = None) -> OpportunityAnalysis:
        candidate = inputs or OpportunityInputs(cluster_id=cluster_id)
        candidate.cluster_id = cluster_id
        result = self.scorer.score(candidate)
        analysis = OpportunityAnalysis.from_result(result)
        if self.repository is not None and cluster_id is not None:
            run = type("OpportunityRun", (), {"model_version": self.model_version, "weights": self.config.dimension_weights, "configuration": {"algorithm": "weighted_opportunity_score", "version": self.model_version}, "cluster_count": 1, "started_at": datetime.now(timezone.utc), "completed_at": datetime.now(timezone.utc), "id": None})()
            analysis.run_id = getattr(run, "id", None)
            if not hasattr(candidate, "source_models"):
                candidate.source_models = {}
        return analysis

    def analyze(self, clusters: list[object]) -> OpportunityAnalysisResult:
        started_at = datetime.now(timezone.utc)
        run = type("OpportunityRun", (), {"model_version": self.model_version, "weights": self.config.dimension_weights, "configuration": {"algorithm": "weighted_opportunity_score", "version": self.model_version}, "cluster_count": len(clusters), "started_at": started_at, "completed_at": datetime.now(timezone.utc), "id": None})()
        if self.repository is not None:
            self.repository.save_opportunity_run(run)

        scores: list[OpportunityAnalysis] = []
        for cluster in clusters:
            cluster_id = getattr(cluster, "id", None)
            latest_inputs = OpportunityInputs(cluster_id=cluster_id)
            if self.repository is not None and cluster_id is not None:
                latest_demand = self.repository.latest_cluster_demand_score(cluster_id)
                latest_competition = self.repository.latest_cluster_competition_score(cluster_id)
                latest_purchase = self.repository.latest_cluster_purchase_intent_score(cluster_id)
                latest_build = self.repository.latest_cluster_build_ease_score(cluster_id)
                latest_diff = self.repository.latest_cluster_differentiation_score(cluster_id)
                if latest_demand is not None:
                    latest_inputs.demand_score = latest_demand.get("demand_score")
                    latest_inputs.demand_confidence = latest_demand.get("confidence")
                    latest_inputs.demand_evidence_coverage = latest_demand.get("evidence_coverage")
                    latest_inputs.demand_analysis_id = latest_demand.get("id")
                    latest_inputs.demand_model_version = latest_demand.get("model_version")
                if latest_competition is not None:
                    latest_inputs.competition_score = latest_competition.get("competition_score")
                    latest_inputs.competition_confidence = latest_competition.get("confidence")
                    latest_inputs.competition_evidence_coverage = latest_competition.get("evidence_coverage")
                    latest_inputs.competition_analysis_id = latest_competition.get("id")
                    latest_inputs.competition_model_version = latest_competition.get("model_version")
                if latest_purchase is not None:
                    latest_inputs.purchase_intent_score = latest_purchase.get("purchase_intent_score")
                    latest_inputs.purchase_intent_confidence = latest_purchase.get("confidence")
                    latest_inputs.purchase_intent_evidence_coverage = latest_purchase.get("evidence_coverage")
                    latest_inputs.purchase_intent_analysis_id = latest_purchase.get("id")
                    latest_inputs.purchase_intent_model_version = latest_purchase.get("model_version")
                if latest_build is not None:
                    latest_inputs.build_ease_score = latest_build.get("build_ease_score")
                    latest_inputs.build_ease_confidence = latest_build.get("confidence")
                    latest_inputs.build_ease_evidence_coverage = latest_build.get("evidence_coverage")
                    latest_inputs.build_ease_analysis_id = latest_build.get("id")
                    latest_inputs.build_ease_model_version = latest_build.get("model_version")
                if latest_diff is not None:
                    latest_inputs.differentiation_score = latest_diff.get("differentiation_score")
                    latest_inputs.differentiation_confidence = latest_diff.get("confidence")
                    latest_inputs.differentiation_evidence_coverage = latest_diff.get("evidence_coverage")
                    latest_inputs.differentiation_analysis_id = latest_diff.get("id")
                    latest_inputs.differentiation_model_version = latest_diff.get("model_version")

            result = self.scorer.score(latest_inputs)
            analysis = OpportunityAnalysis.from_result(result)
            analysis.model_version = self.model_version
            result.model_version = self.model_version
            if self.repository is not None and cluster_id is not None:
                score_payload = type("OpportunityRecord", (), {
                    "cluster_id": cluster_id,
                    "opportunity_score": result.opportunity_score,
                    "status": result.status,
                    "qualification": result.qualification,
                    "opportunity_confidence": result.opportunity_confidence,
                    "dimension_coverage": result.dimension_coverage,
                    "evidence_coverage": result.evidence_coverage,
                    "ranking_eligible": result.ranking_eligible,
                    "components": result.components,
                    "source_analysis_ids": result.source_analysis_ids,
                    "source_model_versions": result.source_model_versions,
                    "bottlenecks": result.bottlenecks,
                    "strongest_dimension": result.strongest_dimension,
                    "weakest_dimension": result.weakest_dimension,
                    "fatal_weaknesses": result.fatal_weaknesses,
                    "warnings": result.warnings,
                    "model_version": self.model_version,
                    "calculated_at": datetime.now(timezone.utc),
                    "run_id": run.id,
                    "id": None,
                })()
                self.repository.save_cluster_opportunity_score(score_payload)
            scores.append(analysis)
        return OpportunityAnalysisResult(run=run, scores=scores)

    def score_with_weights(self, inputs: OpportunityInputs, weights: dict[str, float]) -> OpportunityScoreResult:
        config = OpportunityScoreConfig(
            demand_weight=weights.get("demand", 0.30),
            purchase_intent_weight=weights.get("purchase_intent", 0.20),
            competition_weight=weights.get("competition", 0.15),
            differentiation_weight=weights.get("differentiation", 0.15),
            build_ease_weight=weights.get("build_ease", 0.10),
            price_potential_weight=weights.get("price_potential", 0.10),
        )
        return OpportunityScorer(config).score(inputs)
