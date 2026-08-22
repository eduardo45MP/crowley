from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from crawler.clustering import ProductCluster
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from market_intelligence.purchase_intent.features import PurchaseIntentFeatureExtractor
from market_intelligence.purchase_intent.models import ClusterPurchaseIntentScore, PurchaseIntentAnalysisRun
from market_intelligence.purchase_intent.scoring import PurchaseIntentScorer


@dataclass(slots=True)
class PurchaseIntentAnalysisResult:
    run: PurchaseIntentAnalysisRun
    scores: list[ClusterPurchaseIntentScore]


class PurchaseIntentAnalysisService:
    def __init__(self, repository: SqlAlchemyProductRepository | None = None, model_version: str = "purchase-intent-v1") -> None:
        self.repository = repository
        self.model_version = model_version
        self.extractor = PurchaseIntentFeatureExtractor()
        self.scorer = PurchaseIntentScorer()

    def analyze_cluster(self, cluster: ProductCluster) -> ClusterPurchaseIntentScore:
        features = self.extractor.extract(cluster)
        score, confidence, coverage, components, penalties, weights = self.scorer.score(features)
        warnings = list(features.warnings)
        if features.problem_type == "generic":
            warnings.append("problem is generic; purchase intent evidence is weak")
        if features.buyer_type == "unknown":
            warnings.append("buyer context not resolved")
        if features.workflow_trigger is None:
            warnings.append("workflow trigger not resolved")

        result = ClusterPurchaseIntentScore.from_features(
            cluster_id=cluster.id,
            features=features,
            run_id=None,
            model_version=self.model_version,
            purchase_intent_score=score,
            confidence=confidence,
            evidence_coverage=coverage,
            components={**components, "weights": weights},
            penalties=penalties,
            warnings=warnings,
        )
        return result

    def analyze(self, clusters: list[ProductCluster]) -> PurchaseIntentAnalysisResult:
        started_at = datetime.now(timezone.utc)
        run = PurchaseIntentAnalysisRun(
            model_version=self.model_version,
            configuration={
                "algorithm": "deterministic_purchase_intent_score",
                "version": self.model_version,
            },
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        if self.repository is not None:
            self.repository.save_purchase_intent_run(run)

        scores: list[ClusterPurchaseIntentScore] = []
        for cluster in clusters:
            score = self.analyze_cluster(cluster)
            score.run_id = run.id
            if self.repository is not None:
                self.repository.save_cluster_purchase_intent_score(score)
            scores.append(score)
        return PurchaseIntentAnalysisResult(run=run, scores=scores)
