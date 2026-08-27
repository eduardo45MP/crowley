from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PricingSummary:
    minimum_observed_price: float | None = None
    median_observed_price: float | None = None
    maximum_observed_price: float | None = None
    recommended_price: float | None = None
    currency: str | None = None
    model_version: str = "editorial-pricing-v1"


@dataclass(frozen=True, slots=True)
class CommercialPositioning:
    suggested_product_name: str | None = None
    target_buyer: str | None = None
    pain: str | None = None
    benefit: str | None = None
    primary_differentiator: str | None = None
    value_proposition: str | None = None
    short_positioning_statement: str | None = None
    model_version: str = "editorial-positioning-v1"


@dataclass(slots=True)
class PublishedOpportunity:
    rank: int
    cluster_id: int
    product_name: str | None = None
    product_type: str | None = None
    niche: str | None = None
    buyer_group: str | None = None
    primary_problem: str | None = None
    demand_score: float | None = None
    competition_score: float | None = None
    purchase_intent_score: float | None = None
    build_ease_score: float | None = None
    differentiation_score: float | None = None
    price_potential_score: float | None = None
    opportunity_score: float | None = None
    opportunity_confidence: float | None = None
    selection_rank: int | None = None
    top10_rank: int | None = None
    target_buyer: str | None = None
    problem: str | None = None
    value_proposition: str | None = None
    positioning: str | None = None
    differentiation: str | None = None
    price_min: float | None = None
    price_median: float | None = None
    price_max: float | None = None
    recommended_price: float | None = None
    price_currency: str | None = None
    keywords: list[str] = field(default_factory=list)
    estimated_build_hours: float | None = None
    build_complexity: str | None = None
    scope_level: str | None = None
    revenue_efficiency_score: float | None = None
    research_confidence: float | None = None
    research_coverage: float | None = None
    thesis: dict[str, Any] | None = None
    blueprint: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    model_versions: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReportSnapshot:
    report_id: str
    created_at: datetime
    application_version: str
    database_schema: str
    selection_run_id: int
    deep_research_run_id: int | None
    top10_run_id: int | None
    model_versions: dict[str, str]
    opportunity_count: int
    top10_count: int
    requested_opportunity_count: int
    requested_top10_count: int
    methodology_version: str
    observation_metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        return payload


@dataclass(slots=True)
class PublishedReport:
    snapshot: ReportSnapshot
    ranking: list[PublishedOpportunity]
    top10: list[PublishedOpportunity]
    methodology: dict[str, Any]
    provenance: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        scores = [item.opportunity_score for item in self.ranking if item.opportunity_score is not None]
        summary = {
            "opportunity_count": len(self.ranking),
            "top10_count": len(self.top10),
            "requested_opportunity_count": self.snapshot.requested_opportunity_count,
            "available_opportunity_count": len(self.ranking),
            "fewer_than_requested": len(self.ranking) < self.snapshot.requested_opportunity_count,
            "average_opportunity_score": round(sum(scores) / len(scores), 4) if scores else None,
        }
        return {
            "metadata": self.snapshot.as_dict(),
            "methodology": self.methodology,
            "summary": summary,
            "top10": [item.as_dict() for item in self.top10],
            "ranking": [item.as_dict() for item in self.ranking],
            "provenance": self.provenance,
        }
