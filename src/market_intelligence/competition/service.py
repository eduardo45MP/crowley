from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from crawler.clustering import ProductCluster
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.competition.models import ClusterCompetitionScore, CompetitionAnalysisRun, CompetitionFeatures
from market_intelligence.competition.scoring import CompetitionScorer
from market_intelligence.competition.features import CompetitionFeatureExtractor


@dataclass(slots=True)
class CompetitionAnalysisResult:
    run: CompetitionAnalysisRun
    scores: list[ClusterCompetitionScore]


class CompetitionAnalysisService:
    def __init__(self, repository: SqlAlchemyProductRepository | None = None, model_version: str = "competition-v1") -> None:
        self.repository = repository
        self.model_version = model_version
        self.extractor = CompetitionFeatureExtractor()
        self.scorer = CompetitionScorer()

    def analyze_cluster(self, cluster: ProductCluster) -> ClusterCompetitionScore:
        features = self.extractor.extract(cluster)
        score, confidence, coverage, components, weights = self.scorer.score(features)
        warnings: list[str] = []
        if (features.competitor_count or 0) <= 1:
            warnings.append("cluster pequeno demais para inferir ambiente competitivo")
        if features.seller_count is not None and features.competitor_count and features.seller_count >= max(1, features.competitor_count * 0.8):
            warnings.append("seller concentration baixa: mercado fragmentado")
        if features.price_mean is None:
            warnings.append("preços ausentes para análise de estrutura de mercado")
        if features.rating_mean is None:
            warnings.append("ratings ausentes para análise de qualidade competitiva")
        if features.marketplace_count is not None and features.marketplace_count == 1:
            warnings.append("dados restritos a um único marketplace")

        result = ClusterCompetitionScore.from_features(
            cluster_id=cluster.id,
            features=features,
            run_id=None,
            model_version=self.model_version,
            competition_score=score,
            confidence=confidence,
            evidence_coverage=coverage,
            components={**components, "weights": weights},
            warnings=warnings,
        )
        if self.repository is not None:
            result.run_id = None
        return result

    def analyze(self, clusters: list[ProductCluster]) -> CompetitionAnalysisResult:
        started_at = datetime.now(timezone.utc)
        run = CompetitionAnalysisRun(
            model_version=self.model_version,
            configuration={
                "algorithm": "deterministic_competition_score",
                "version": self.model_version,
            },
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        if self.repository is not None:
            self.repository.save_competition_run(run)

        scores: list[ClusterCompetitionScore] = []
        for cluster in clusters:
            score = self.analyze_cluster(cluster)
            score.run_id = run.id
            if self.repository is not None:
                self.repository.save_cluster_competition_score(score)
            scores.append(score)
        return CompetitionAnalysisResult(run=run, scores=scores)
