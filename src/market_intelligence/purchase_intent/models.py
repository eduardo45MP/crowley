from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class PurchaseIntentAnalysisRun:
    model_version: str
    configuration: dict[str, Any]
    cluster_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class PurchaseIntentFeatures:
    financial_impact_score: float | None = None
    usage_frequency_score: float | None = None
    cost_of_error_score: float | None = None
    urgency_score: float | None = None
    perceived_value_score: float | None = None
    commercial_context_score: float | None = None
    workflow_criticality_score: float | None = None
    repeatability_score: float | None = None
    replacement_cost_score: float | None = None
    llm_substitutability: float | None = None
    free_alternative_pressure: float | None = None
    problem_type: str | None = None
    buyer_type: str | None = None
    workflow_trigger: str | None = None
    consequences: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClusterPurchaseIntentScore:
    cluster_id: int | None
    purchase_intent_score: float
    confidence: float
    evidence_coverage: float
    features: dict[str, Any]
    components: dict[str, Any]
    penalties: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    model_version: str = "purchase-intent-v1"
    calculated_at: datetime | None = None
    run_id: int | None = None
    id: int | None = None

    @classmethod
    def from_features(
        cls,
        *,
        cluster_id: int | None,
        features: PurchaseIntentFeatures,
        run_id: int | None,
        model_version: str,
        purchase_intent_score: float,
        confidence: float,
        evidence_coverage: float,
        components: dict[str, Any],
        penalties: dict[str, float],
        warnings: list[str],
    ) -> "ClusterPurchaseIntentScore":
        payload: dict[str, Any] = {
            "financial_impact_score": features.financial_impact_score,
            "usage_frequency_score": features.usage_frequency_score,
            "cost_of_error_score": features.cost_of_error_score,
            "urgency_score": features.urgency_score,
            "perceived_value_score": features.perceived_value_score,
            "commercial_context_score": features.commercial_context_score,
            "workflow_criticality_score": features.workflow_criticality_score,
            "repeatability_score": features.repeatability_score,
            "replacement_cost_score": features.replacement_cost_score,
            "llm_substitutability": features.llm_substitutability,
            "free_alternative_pressure": features.free_alternative_pressure,
            "problem_type": features.problem_type,
            "buyer_type": features.buyer_type,
            "workflow_trigger": features.workflow_trigger,
            "consequences": features.consequences,
            "warnings": features.warnings,
        }
        return cls(
            cluster_id=cluster_id,
            purchase_intent_score=purchase_intent_score,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            features=payload,
            components=components,
            penalties=penalties,
            warnings=warnings,
            model_version=model_version,
            calculated_at=datetime.now(timezone.utc),
            run_id=run_id,
        )
