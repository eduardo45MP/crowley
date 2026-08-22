from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DifferentiationAnalysisRun:
    model_version: str
    configuration: dict[str, Any]
    cluster_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class DifferentiationFeatures:
    feature_gap: float = 0.0
    complaint_gap: float = 0.0
    product_depth_gap: float = 0.0
    customization_gap: float = 0.0
    automation_gap: float = 0.0
    ux_gap: float = 0.0
    visual_quality_gap: float = 0.0
    documentation_gap: float = 0.0
    internationalization_gap: float = 0.0
    positioning_gap: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClusterDifferentiationScore:
    cluster_id: int | None
    differentiation_score: float
    confidence: float
    evidence_coverage: float
    features: dict[str, Any]
    components: dict[str, Any]
    model_version: str
    calculated_at: datetime | None = None
    run_id: int | None = None
    id: int | None = None

    @classmethod
    def from_features(
        cls,
        *,
        cluster_id: int | None,
        features: DifferentiationFeatures,
        run_id: int | None,
        model_version: str,
        differentiation_score: float,
        confidence: float,
        evidence_coverage: float,
        components: dict[str, Any],
    ) -> "ClusterDifferentiationScore":
        return cls(
            cluster_id=cluster_id,
            differentiation_score=differentiation_score,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            features={
                "feature_gap": features.feature_gap,
                "complaint_gap": features.complaint_gap,
                "product_depth_gap": features.product_depth_gap,
                "customization_gap": features.customization_gap,
                "automation_gap": features.automation_gap,
                "ux_gap": features.ux_gap,
                "visual_quality_gap": features.visual_quality_gap,
                "documentation_gap": features.documentation_gap,
                "internationalization_gap": features.internationalization_gap,
                "positioning_gap": features.positioning_gap,
                "notes": features.notes,
            },
            components=components,
            model_version=model_version,
            calculated_at=datetime.now(timezone.utc),
            run_id=run_id,
        )
