from __future__ import annotations

from typing import Any

from crawler.clustering import ProductCluster
from market_intelligence.demand.features import DemandFeaturesExtractor


class DemandScorer:
    def __init__(self) -> None:
        self.extractor = DemandFeaturesExtractor()

    def score(self, cluster: ProductCluster) -> tuple[float, float, float, dict[str, Any], dict[str, Any]]:
        features = self.extractor.extract(cluster)
        base = 0.0
        if cluster.niche and cluster.niche.lower() not in {"misc", "unknown", "generic"}:
            base += 18.0
        if cluster.primary_problem:
            base += 18.0
        if cluster.product_type:
            base += 14.0
        base += min(22.0, (cluster.product_count * 6.0))
        base += min(18.0, float(cluster.confidence or 0.0) * 28.0)
        base += min(16.0, float(features["review_velocity"]) / 3.0)
        base += min(20.0, float(features["signal_density"]) * 30.0)

        confidence = min(1.0, (float(cluster.confidence or 0.0) * 0.5) + (float(features["signal_density"]) * 0.5))
        coverage = min(1.0, max(float(features["evidence_coverage"]), float(cluster.confidence or 0.0) * 0.5))

        score = max(0.0, min(100.0, base * (0.65 + coverage * 0.35)))
        components = {
            "base": round(base, 4),
            "cluster_size_weight": round(min(22.0, cluster.product_count * 6.0), 4),
            "confidence_weight": round(min(18.0, float(cluster.confidence or 0.0) * 28.0), 4),
            "signal_density_weight": round(min(20.0, float(features["signal_density"]) * 30.0), 4),
            "review_velocity_weight": round(min(16.0, float(features["review_velocity"]) / 3.0), 4),
        }
        return score, confidence, coverage, features, components
