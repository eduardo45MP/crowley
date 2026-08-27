from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DeepResearchVerdict:
    cluster_id: int | None
    thesis_strength: float | None = None
    evidence_strength: float | None = None
    differentiation_clarity: float | None = None
    product_clarity: float | None = None
    contradiction_severity: float | None = None
    research_confidence: float | None = None
    verdict: str = "mixed"


@dataclass(slots=True)
class Top10Opportunity:
    cluster_id: int | None
    cluster_name: str | None = None
    top10_rank: int = 0
    opportunity_score: float | None = None
    top10_selection_utility: float | None = None
    deep_research_verdict: str = "mixed"
    research_confidence: float | None = None
    selection_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    selected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "top10_rank": self.top10_rank,
            "opportunity_score": self.opportunity_score,
            "top10_selection_utility": self.top10_selection_utility,
            "deep_research_verdict": self.deep_research_verdict,
            "research_confidence": self.research_confidence,
            "selection_reasons": list(self.selection_reasons),
            "warnings": list(self.warnings),
            "selected_at": self.selected_at.isoformat(),
        }


@dataclass(slots=True)
class Top10SelectionRun:
    id: int | None = None
    deep_research_run_id: int | None = None
    model_version: str = "top10-selection-v1"
    configuration: dict[str, Any] = field(default_factory=dict)
    candidate_count: int = 0
    selected_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(slots=True)
class Top10SelectionResult:
    run: Top10SelectionRun
    selected: list[Top10Opportunity]
    rejected: list[DeepResearchVerdict]
    diagnostics: dict[str, Any]


@dataclass(slots=True)
class OpportunityThesis:
    cluster_id: int | None
    target_buyer: str = "unknown"
    problem: str = "unknown"
    market_evidence: list[str] = field(default_factory=list)
    buyer_evidence: list[str] = field(default_factory=list)
    competitor_weaknesses: list[str] = field(default_factory=list)
    critical_gaps: list[str] = field(default_factory=list)
    proposed_advantage: list[str] = field(default_factory=list)
    opportunity_statement: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "target_buyer": self.target_buyer,
            "problem": self.problem,
            "market_evidence": list(self.market_evidence),
            "buyer_evidence": list(self.buyer_evidence),
            "competitor_weaknesses": list(self.competitor_weaknesses),
            "critical_gaps": list(self.critical_gaps),
            "proposed_advantage": list(self.proposed_advantage),
            "opportunity_statement": self.opportunity_statement,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }
