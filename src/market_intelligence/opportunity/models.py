from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class OpportunityInputs:
    cluster_id: int | None
    demand_score: float | None = None
    purchase_intent_score: float | None = None
    competition_score: float | None = None
    differentiation_score: float | None = None
    build_ease_score: float | None = None
    price_potential_score: float | None = None
    demand_confidence: float | None = None
    purchase_intent_confidence: float | None = None
    competition_confidence: float | None = None
    differentiation_confidence: float | None = None
    build_ease_confidence: float | None = None
    price_potential_confidence: float | None = None
    demand_evidence_coverage: float | None = None
    purchase_intent_evidence_coverage: float | None = None
    competition_evidence_coverage: float | None = None
    differentiation_evidence_coverage: float | None = None
    build_ease_evidence_coverage: float | None = None
    price_potential_evidence_coverage: float | None = None
    demand_analysis_id: int | None = None
    purchase_intent_analysis_id: int | None = None
    competition_analysis_id: int | None = None
    differentiation_analysis_id: int | None = None
    build_ease_analysis_id: int | None = None
    price_potential_analysis_id: int | None = None
    demand_model_version: str | None = None
    purchase_intent_model_version: str | None = None
    competition_model_version: str | None = None
    differentiation_model_version: str | None = None
    build_ease_model_version: str | None = None
    price_potential_model_version: str | None = None
    source_models: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class OpportunityScoreResult:
    cluster_id: int | None
    opportunity_score: float | None
    status: str
    qualification: str | None
    opportunity_confidence: float | None
    dimension_coverage: float
    evidence_coverage: float | None
    components: dict[str, float]
    source_analysis_ids: dict[str, int | None]
    source_model_versions: dict[str, str | None]
    bottlenecks: list[str]
    strongest_dimension: str | None
    weakest_dimension: str | None
    fatal_weaknesses: list[str]
    ranking_eligible: bool
    model_version: str = "opportunity-v1"
    calculated_at: datetime | None = None
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "opportunity_score": self.opportunity_score,
            "status": self.status,
            "qualification": self.qualification,
            "opportunity_confidence": self.opportunity_confidence,
            "dimension_coverage": self.dimension_coverage,
            "evidence_coverage": self.evidence_coverage,
            "components": self.components,
            "source_analysis_ids": self.source_analysis_ids,
            "source_model_versions": self.source_model_versions,
            "bottlenecks": self.bottlenecks,
            "strongest_dimension": self.strongest_dimension,
            "weakest_dimension": self.weakest_dimension,
            "fatal_weaknesses": self.fatal_weaknesses,
            "ranking_eligible": self.ranking_eligible,
            "model_version": self.model_version,
            "calculated_at": self.calculated_at,
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class OpportunityAnalysis:
    cluster_id: int | None
    opportunity_score: float | None
    status: str
    qualification: str | None
    opportunity_confidence: float | None
    dimension_coverage: float
    evidence_coverage: float | None
    components: dict[str, float]
    source_analysis_ids: dict[str, int | None]
    source_model_versions: dict[str, str | None]
    bottlenecks: list[str]
    strongest_dimension: str | None
    weakest_dimension: str | None
    fatal_weaknesses: list[str]
    ranking_eligible: bool
    model_version: str = "opportunity-v1"
    calculated_at: datetime | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_result(cls, result: OpportunityScoreResult) -> "OpportunityAnalysis":
        return cls(
            cluster_id=result.cluster_id,
            opportunity_score=result.opportunity_score,
            status=result.status,
            qualification=result.qualification,
            opportunity_confidence=result.opportunity_confidence,
            dimension_coverage=result.dimension_coverage,
            evidence_coverage=result.evidence_coverage,
            components=result.components,
            source_analysis_ids=result.source_analysis_ids,
            source_model_versions=result.source_model_versions,
            bottlenecks=result.bottlenecks,
            strongest_dimension=result.strongest_dimension,
            weakest_dimension=result.weakest_dimension,
            fatal_weaknesses=result.fatal_weaknesses,
            ranking_eligible=result.ranking_eligible,
            model_version=result.model_version,
            calculated_at=result.calculated_at or datetime.now(timezone.utc),
            warnings=result.warnings,
        )
