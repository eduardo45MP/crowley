from __future__ import annotations

import math

from market_intelligence.competition.config import CompetitionConfig
from market_intelligence.competition.models import CompetitionFeatures


def competition_density_attractiveness(competitor_count: int, *, target: int = 24, low_end: int = 2, high_end: int = 180) -> float:
    if competitor_count <= 0:
        return 0.0
    if competitor_count <= low_end:
        return min(1.0, 0.18 + (competitor_count / max(1, low_end)) * 0.72)
    if competitor_count <= target:
        return max(0.55, 1.0 - ((competitor_count - low_end) / max(1, target - low_end)) * 0.45)
    if competitor_count <= high_end:
        return max(0.15, 0.72 - ((competitor_count - target) / max(1, high_end - target)) * 0.57)
    return max(0.0, 0.18 - ((competitor_count - high_end) / max(1, 1000)) * 0.18)


class CompetitionScorer:
    def __init__(self, config: CompetitionConfig | None = None) -> None:
        self.config = config or CompetitionConfig()

    def score(self, features: CompetitionFeatures) -> tuple[float, float, float, dict[str, float], dict[str, float]]:
        density = competition_density_attractiveness(features.competitor_count or 0, target=self.config.target_competitor_count, low_end=self.config.density_low_count, high_end=self.config.density_high_count)
        fragmentation = features.market_fragmentation if features.market_fragmentation is not None else 0.0
        review_favorability = 1.0 - (features.top_seller_review_share or 0.0)
        price_favorability = 0.5
        if features.price_band_opportunity is not None:
            price_favorability = max(0.0, min(1.0, features.price_band_opportunity))
        if features.price_compression is not None:
            price_favorability = max(0.0, min(1.0, price_favorability * (1.0 - features.price_compression)))

        quality_imperfection = 1.0 - (features.competitor_quality_signal or 0.0)
        depth_gap = features.product_depth_signal or 0.0
        differentiation_gap = features.observed_differentiation_signal or 0.0

        components = {
            "competitive_density_attractiveness": density,
            "market_fragmentation": fragmentation,
            "review_concentration_favorability": review_favorability,
            "price_structure_favorability": price_favorability,
            "competitor_quality_imperfection": quality_imperfection,
            "product_depth_gap": depth_gap,
            "observed_differentiation_gap": differentiation_gap,
        }

        weights = {
            "competitive_density_attractiveness": 0.20,
            "market_fragmentation": 0.20,
            "review_concentration_favorability": 0.15,
            "price_structure_favorability": 0.15,
            "competitor_quality_imperfection": 0.10,
            "product_depth_gap": 0.10,
            "observed_differentiation_gap": 0.10,
        }

        available = {key: value for key, value in components.items() if value is not None}
        if not available:
            score = 0.0
            confidence = 0.0
            coverage = 0.0
            return score, confidence, coverage, components, weights

        coverage = min(1.0, len(available) / 7.0)
        weighted_total = sum((components[key] * weights[key]) for key in weights if key in available)
        total_weight = sum(weights[key] for key in weights if key in available)
        score_value = (weighted_total / total_weight) * 100.0
        score_value = max(0.0, min(100.0, score_value))

        confidence = min(
            1.0,
            coverage * 0.7 + (1.0 if (features.competitor_count or 0) >= 5 else 0.4) * 0.3,
        )
        return score_value, confidence, coverage, {key: round(value, 4) for key, value in components.items()}, {key: round(value, 4) for key, value in weights.items()}
