from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DemandAnalysisRun:
    model_version: str
    configuration: dict[str, Any]
    cluster_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class DemandFeatures:
    keywords: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    primary_problem: str | None = None
    product_type: str | None = None
    niche: str | None = None
    review_velocity: float = 0.0
    cluster_size: int = 0
    confidence: float = 0.0
    signal_density: float = 0.0
    evidence_coverage: float = 0.0


@dataclass(slots=True)
class ClusterDemandScore:
    cluster_id: int | None
    demand_score: float
    confidence: float
    evidence_coverage: float
    features: dict[str, Any]
    components: dict[str, Any]
    model_version: str
    calculated_at: datetime | None = None
    run_id: int | None = None
    id: int | None = None

    @classmethod
    def from_features(cls, *, cluster_id: int | None, features: DemandFeatures | dict[str, Any], run_id: int | None, model_version: str, score: float, confidence: float, evidence_coverage: float, components: dict[str, Any]) -> "ClusterDemandScore":
        if isinstance(features, dict):
            feature_payload = features
        else:
            feature_payload = {
                "keywords": features.keywords,
                "signals": features.signals,
                "primary_problem": features.primary_problem,
                "product_type": features.product_type,
                "niche": features.niche,
                "review_velocity": features.review_velocity,
                "cluster_size": features.cluster_size,
                "confidence": features.confidence,
                "signal_density": features.signal_density,
            }
        return cls(
            cluster_id=cluster_id,
            demand_score=score,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            features=feature_payload,
            components=components,
            model_version=model_version,
            calculated_at=datetime.now(timezone.utc),
            run_id=run_id,
        )
