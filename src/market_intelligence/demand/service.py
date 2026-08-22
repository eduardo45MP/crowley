from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from crawler.clustering import ProductCluster
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.demand.models import ClusterDemandScore, DemandAnalysisRun
from market_intelligence.demand.scoring import DemandScorer


@dataclass(slots=True)
class DemandCalculationResult:
    run: DemandAnalysisRun
    scores: list[ClusterDemandScore]


class DemandScoringService:
    def __init__(self, repository: SqlAlchemyProductRepository | None = None, model_version: str = "v1") -> None:
        self.repository = repository
        self.model_version = model_version
        self.scorer = DemandScorer()

    def score_cluster(self, cluster: ProductCluster) -> ClusterDemandScore:
        score, confidence, coverage, features, components = self.scorer.score(cluster)
        return ClusterDemandScore.from_features(
            cluster_id=cluster.id,
            features=self._as_features(features),
            run_id=None,
            model_version=self.model_version,
            score=score,
            confidence=confidence,
            evidence_coverage=coverage,
            components=components,
        )

    def calculate(self, clusters: list[ProductCluster]) -> DemandCalculationResult:
        started_at = datetime.now(timezone.utc)
        run = DemandAnalysisRun(
            model_version=self.model_version,
            configuration={
                "algorithm": "deterministic_signal_score",
                "version": self.model_version,
                "minimum_cluster_size": 1,
            },
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        if self.repository is not None:
            self.repository.save_demand_run(run)

        scores: list[ClusterDemandScore] = []
        for cluster in clusters:
            score = self.score_cluster(cluster)
            score.run_id = run.id
            if self.repository is not None:
                self.repository.save_cluster_demand_score(score)
            scores.append(score)

        return DemandCalculationResult(run=run, scores=scores)

    @staticmethod
    def _as_features(raw: dict[str, Any]) -> Any:
        return {
            "keywords": list(raw.get("keywords", [])),
            "signals": list(raw.get("signals", [])),
            "primary_problem": raw.get("primary_problem"),
            "product_type": raw.get("product_type"),
            "niche": raw.get("niche"),
            "review_velocity": float(raw.get("review_velocity", 0.0)),
            "cluster_size": int(raw.get("cluster_size", 0)),
            "confidence": float(raw.get("confidence", 0.0)),
            "signal_density": float(raw.get("signal_density", 0.0)),
        }
