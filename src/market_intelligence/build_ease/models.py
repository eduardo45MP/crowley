from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class BuildEaseAnalysisRun:
    model_version: str
    configuration: dict[str, Any]
    cluster_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class BuildEaseFeatures:
    tab_count: float = 0.0
    formula_difficulty: float = 0.0
    api_dependency: float = 0.0
    external_data_need: float = 0.0
    design_complexity: float = 0.0
    maintenance_need: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClusterBuildEaseScore:
    cluster_id: int | None
    build_ease_score: float
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
        features: BuildEaseFeatures,
        run_id: int | None,
        model_version: str,
        build_ease_score: float,
        confidence: float,
        evidence_coverage: float,
        components: dict[str, Any],
    ) -> "ClusterBuildEaseScore":
        return cls(
            cluster_id=cluster_id,
            build_ease_score=build_ease_score,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            features={
                "tab_count": features.tab_count,
                "formula_difficulty": features.formula_difficulty,
                "api_dependency": features.api_dependency,
                "external_data_need": features.external_data_need,
                "design_complexity": features.design_complexity,
                "maintenance_need": features.maintenance_need,
                "notes": features.notes,
            },
            components=components,
            model_version=model_version,
            calculated_at=datetime.now(timezone.utc),
            run_id=run_id,
        )
