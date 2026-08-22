from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from crawler.clustering import ProductCluster
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.build_ease.features import BuildEaseFeatureExtractor
from market_intelligence.build_ease.models import BuildEaseAnalysisRun, ClusterBuildEaseScore
from market_intelligence.build_ease.scoring import BuildEaseScorer


@dataclass(slots=True)
class BuildEaseAnalysisResult:
    run: BuildEaseAnalysisRun
    scores: list[ClusterBuildEaseScore]


class BuildEaseAnalysisService:
    def __init__(self, repository: SqlAlchemyProductRepository | None = None, model_version: str = "build-ease-v1") -> None:
        self.repository = repository
        self.model_version = model_version
        self.extractor = BuildEaseFeatureExtractor()
        self.scorer = BuildEaseScorer()

    def analyze_cluster(self, cluster: ProductCluster) -> ClusterBuildEaseScore:
        features = self.extractor.extract(cluster)
        score, confidence, coverage, components, weights = self.scorer.score(features)
        return ClusterBuildEaseScore.from_features(
            cluster_id=cluster.id,
            features=features,
            run_id=None,
            model_version=self.model_version,
            build_ease_score=score,
            confidence=confidence,
            evidence_coverage=coverage,
            components={**components, "weights": weights},
        )

    def analyze(self, clusters: list[ProductCluster]) -> BuildEaseAnalysisResult:
        started_at = datetime.now(timezone.utc)
        run = BuildEaseAnalysisRun(
            model_version=self.model_version,
            configuration={
                "algorithm": "deterministic_build_ease_score",
                "version": self.model_version,
            },
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        if self.repository is not None:
            self.repository.save_build_ease_run(run)

        scores: list[ClusterBuildEaseScore] = []
        for cluster in clusters:
            score = self.analyze_cluster(cluster)
            score.run_id = run.id
            if self.repository is not None:
                self.repository.save_cluster_build_ease_score(score)
            scores.append(score)
        return BuildEaseAnalysisResult(run=run, scores=scores)
