from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class CompetitionAnalysisRun:
    model_version: str
    configuration: dict[str, Any]
    cluster_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class CompetitionFeatures:
    competitor_count: int | None = None
    seller_count: int | None = None
    marketplace_count: int | None = None
    top_seller_listing_share: float | None = None
    top_seller_review_share: float | None = None
    top_3_review_share: float | None = None
    market_fragmentation: float | None = None
    price_min: Decimal | None = None
    price_median: Decimal | None = None
    price_max: Decimal | None = None
    price_mean: Decimal | None = None
    price_stddev: Decimal | None = None
    price_cv: float | None = None
    price_compression: float | None = None
    price_band_opportunity: float | None = None
    rating_mean: float | None = None
    rating_median: float | None = None
    competitor_quality_signal: float | None = None
    visual_quality_signal: float | None = None
    product_depth_signal: float | None = None
    observed_differentiation_signal: float | None = None


@dataclass(slots=True)
class ClusterCompetitionScore:
    cluster_id: int | None
    competition_score: float
    confidence: float
    evidence_coverage: float
    features: dict[str, Any]
    components: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    model_version: str = "competition-v1"
    calculated_at: datetime | None = None
    run_id: int | None = None
    id: int | None = None

    @classmethod
    def from_features(
        cls,
        *,
        cluster_id: int | None,
        features: CompetitionFeatures,
        run_id: int | None,
        model_version: str,
        competition_score: float,
        confidence: float,
        evidence_coverage: float,
        components: dict[str, Any],
        warnings: list[str],
    ) -> "ClusterCompetitionScore":
        payload: dict[str, Any] = {
            "competitor_count": features.competitor_count,
            "seller_count": features.seller_count,
            "marketplace_count": features.marketplace_count,
            "top_seller_listing_share": features.top_seller_listing_share,
            "top_seller_review_share": features.top_seller_review_share,
            "top_3_review_share": features.top_3_review_share,
            "market_fragmentation": features.market_fragmentation,
            "price_min": str(features.price_min) if features.price_min is not None else None,
            "price_median": str(features.price_median) if features.price_median is not None else None,
            "price_max": str(features.price_max) if features.price_max is not None else None,
            "price_mean": str(features.price_mean) if features.price_mean is not None else None,
            "price_stddev": str(features.price_stddev) if features.price_stddev is not None else None,
            "price_cv": features.price_cv,
            "price_compression": features.price_compression,
            "price_band_opportunity": features.price_band_opportunity,
            "rating_mean": features.rating_mean,
            "rating_median": features.rating_median,
            "competitor_quality_signal": features.competitor_quality_signal,
            "visual_quality_signal": features.visual_quality_signal,
            "product_depth_signal": features.product_depth_signal,
            "observed_differentiation_signal": features.observed_differentiation_signal,
        }
        return cls(
            cluster_id=cluster_id,
            competition_score=competition_score,
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            features=payload,
            components=components,
            warnings=warnings,
            model_version=model_version,
            calculated_at=datetime.now(timezone.utc),
            run_id=run_id,
        )
