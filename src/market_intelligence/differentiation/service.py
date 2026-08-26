from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from crawler.clustering import ProductCluster
from crawler.repositories import sqlalchemy_repository as repo_module
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.differentiation.features import DifferentiationFeatureExtractor
from market_intelligence.differentiation.models import ClusterDifferentiationScore, DifferentiationAnalysisRun
from market_intelligence.differentiation.scoring import DifferentiationScorer


def _default_differentiation_repository() -> SqlAlchemyProductRepository:
    if repo_module.DEFAULT_SQLITE_REPOSITORY is not None:
        return repo_module.DEFAULT_SQLITE_REPOSITORY
    return SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")


@dataclass(slots=True)
class DifferentiationAnalysisResult:
    run: DifferentiationAnalysisRun
    scores: list[ClusterDifferentiationScore]


class DifferentiationAnalysisService:
    def __init__(self, repository: SqlAlchemyProductRepository | None = None, model_version: str = "differentiation-v1") -> None:
        self.repository = repository or _default_differentiation_repository()
        self.model_version = model_version
        self.extractor = DifferentiationFeatureExtractor()
        self.scorer = DifferentiationScorer()

    def analyze_cluster(self, cluster: ProductCluster) -> ClusterDifferentiationScore:
        features = self.extractor.extract(cluster)
        score, confidence, coverage, components, weights = self.scorer.score(features)
        result = ClusterDifferentiationScore.from_features(
            cluster_id=cluster.id,
            features=features,
            run_id=None,
            model_version=self.model_version,
            differentiation_score=score,
            confidence=confidence,
            evidence_coverage=coverage,
            components={**components, "weights": weights},
        )
        if self.repository is not None:
            run = self.repository.save_differentiation_run(
                DifferentiationAnalysisRun(
                    model_version=self.model_version,
                    configuration={"algorithm": "deterministic_differentiation_score", "version": self.model_version},
                    cluster_count=1,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
            )
            result.run_id = run.id
            self.repository.save_cluster_differentiation_score(result)
        else:
            result.id = int(datetime.now(timezone.utc).timestamp() * 1_000_000) % 1_000_000_000
            result.run_id = result.id
        return result

    def analyze(self, clusters: list[ProductCluster]) -> DifferentiationAnalysisResult:
        started_at = datetime.now(timezone.utc)
        run = DifferentiationAnalysisRun(
            model_version=self.model_version,
            configuration={
                "algorithm": "deterministic_differentiation_score",
                "version": self.model_version,
            },
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        if self.repository is not None:
            self.repository.save_differentiation_run(run)

        scores: list[ClusterDifferentiationScore] = []
        for cluster in clusters:
            score = self.analyze_cluster(cluster)
            score.run_id = run.id
            if self.repository is not None:
                self.repository.save_cluster_differentiation_score(score)
            scores.append(score)
        return DifferentiationAnalysisResult(run=run, scores=scores)
