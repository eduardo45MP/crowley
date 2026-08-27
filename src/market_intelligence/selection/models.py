from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class OpportunityCandidate:
    cluster_id: int | None
    cluster_name: str | None = None
    opportunity_score: float | None = None
    opportunity_confidence: float | None = None
    evidence_coverage: float | None = None
    buyer_group: str | None = None
    niche: str | None = None
    problem_type: str | None = None
    product_type: str | None = None
    demand_score: float | None = None
    competition_score: float | None = None
    purchase_intent_score: float | None = None
    build_ease_score: float | None = None
    differentiation_score: float | None = None
    price_potential_score: float | None = None
    ranking_eligible: bool = True
    selection_utility: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SelectedOpportunity:
    cluster_id: int | None
    cluster_name: str | None
    selection_rank: int
    global_opportunity_rank: int | None = None
    buyer_group: str | None = None
    quota_bucket: str | None = None
    niche: str | None = None
    problem_type: str | None = None
    product_type: str | None = None
    opportunity_score: float | None = None
    opportunity_confidence: float | None = None
    evidence_coverage: float | None = None
    selection_utility: float | None = None
    selection_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    selected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "selection_rank": self.selection_rank,
            "global_opportunity_rank": self.global_opportunity_rank,
            "buyer_group": self.buyer_group,
            "quota_bucket": self.quota_bucket,
            "niche": self.niche,
            "problem_type": self.problem_type,
            "product_type": self.product_type,
            "opportunity_score": self.opportunity_score,
            "opportunity_confidence": self.opportunity_confidence,
            "evidence_coverage": self.evidence_coverage,
            "selection_utility": self.selection_utility,
            "selection_reasons": self.selection_reasons,
            "warnings": self.warnings,
            "selected_at": self.selected_at.isoformat(),
        }


@dataclass(slots=True)
class SelectionRun:
    id: int | None = None
    model_version: str = "selection-v1"
    configuration: dict[str, Any] = field(default_factory=dict)
    candidate_count: int = 0
    eligible_count: int = 0
    selected_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(slots=True)
class SelectionResult:
    run: SelectionRun
    selected: list[SelectedOpportunity]
    rejected: list[OpportunityCandidate]
    portfolio_distribution: dict[str, int]
    diagnostics: dict[str, Any]
