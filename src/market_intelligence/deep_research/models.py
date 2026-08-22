from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ResearchEvidence:
    evidence_type: str
    product_id: int | None = None
    marketplace: str | None = None
    source_url: str | None = None
    raw_value: str | float | int | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float | None = None


@dataclass(slots=True)
class CompetitorProfile:
    competitor_id: str
    product_id: int | None = None
    product_name: str | None = None
    seller: str | None = None
    marketplace: str | None = None
    url: str | None = None
    price: float | None = None
    currency: str | None = None
    rating: float | None = None
    review_count: int | None = None
    keywords: list[str] = field(default_factory=list)
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)
    screenshot_paths: list[str] = field(default_factory=list)
    detected_features: list[str] = field(default_factory=list)
    positioning: dict[str, str] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    review_summary: str | None = None
    complaint_themes: list[str] = field(default_factory=list)
    research_notes: list[str] = field(default_factory=list)
    evidence: list[ResearchEvidence] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "competitor_id": self.competitor_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "seller": self.seller,
            "marketplace": self.marketplace,
            "url": self.url,
            "price": self.price,
            "currency": self.currency,
            "rating": self.rating,
            "review_count": self.review_count,
            "keywords": list(self.keywords),
            "description": self.description,
            "image_urls": list(self.image_urls),
            "screenshot_paths": list(self.screenshot_paths),
            "detected_features": list(self.detected_features),
            "positioning": dict(self.positioning),
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "review_summary": self.review_summary,
            "complaint_themes": list(self.complaint_themes),
            "research_notes": list(self.research_notes),
        }


@dataclass(slots=True)
class PriceAnalysis:
    minimum: float | None = None
    median: float | None = None
    maximum: float | None = None
    mean: float | None = None
    leader_median: float | None = None
    mid_market_median: float | None = None
    entry_level_median: float | None = None
    segments: dict[str, tuple[float, float]] = field(default_factory=dict)
    currency: str | None = None


@dataclass(slots=True)
class FeatureCoverage:
    feature: str
    coverage_ratio: float
    competitors_with_feature: int
    competitors_analyzed: int
    importance: float = 0.0


@dataclass(slots=True)
class KeywordAnalysis:
    top_keywords: list[str] = field(default_factory=list)
    keyword_frequency: dict[str, int] = field(default_factory=dict)
    keyword_variants: dict[str, list[str]] = field(default_factory=dict)
    long_tail_keywords: list[str] = field(default_factory=list)
    intent_classification: dict[str, list[str]] = field(default_factory=dict)
    keyword_gaps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProductStructure:
    product_id: int | None = None
    sheet_count: int | None = None
    sheet_names: list[str] = field(default_factory=list)
    input_sections: list[str] = field(default_factory=list)
    calculation_sections: list[str] = field(default_factory=list)
    output_sections: list[str] = field(default_factory=list)
    dashboards: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    automation_features: list[str] = field(default_factory=list)
    source: str | None = None
    confidence: float | None = None
    evidence: list[ResearchEvidence] = field(default_factory=list)


@dataclass(slots=True)
class ReviewAnalysis:
    reviews_available: bool
    reviews_analyzed: int
    review_coverage: float
    review_analysis_confidence: float
    positive_themes: list[str]
    negative_themes: list[str]
    complaint_themes: list[str]
    complaint_frequency: dict[str, int]
    sample_strategy: str
    status: str = "partial"


@dataclass(slots=True)
class DeepResearchRun:
    id: int | None = None
    selection_run_id: int | None = None
    model_version: str = "deep-research-v1"
    target_count: int = 25
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(slots=True)
class DeepResearchDossier:
    cluster_id: int | None
    cluster_name: str | None
    selection_run_id: int | None = None
    research_rank: int = 0
    competitor_count_analyzed: int = 0
    pricing_analysis: dict[str, Any] = field(default_factory=dict)
    competitor_profiles: list[CompetitorProfile] = field(default_factory=list)
    feature_matrix: dict[str, Any] = field(default_factory=dict)
    review_analysis: dict[str, Any] = field(default_factory=dict)
    keyword_analysis: dict[str, Any] = field(default_factory=dict)
    product_structure_analysis: dict[str, Any] = field(default_factory=dict)
    screenshots: list[dict[str, Any]] = field(default_factory=list)
    market_patterns: list[str] = field(default_factory=list)
    observed_gaps: list[str] = field(default_factory=list)
    differentiation_axes: list[str] = field(default_factory=list)
    confirmations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    research_coverage: float = 0.0
    research_confidence: float = 0.0
    status: str = "pending"
    model_version: str = "deep-research-v1"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "selection_run_id": self.selection_run_id,
            "research_rank": self.research_rank,
            "competitor_count_analyzed": self.competitor_count_analyzed,
            "pricing_analysis": self.pricing_analysis,
            "competitor_profiles": [profile.as_dict() for profile in self.competitor_profiles],
            "feature_matrix": self.feature_matrix,
            "review_analysis": self.review_analysis,
            "keyword_analysis": self.keyword_analysis,
            "product_structure_analysis": self.product_structure_analysis,
            "screenshots": self.screenshots,
            "market_patterns": list(self.market_patterns),
            "observed_gaps": list(self.observed_gaps),
            "differentiation_axes": list(self.differentiation_axes),
            "confirmations": list(self.confirmations),
            "contradictions": list(self.contradictions),
            "warnings": list(self.warnings),
            "research_coverage": self.research_coverage,
            "research_confidence": self.research_confidence,
            "status": self.status,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
