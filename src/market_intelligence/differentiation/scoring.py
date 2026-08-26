from __future__ import annotations

from market_intelligence.differentiation.config import DifferentiationConfig
from market_intelligence.differentiation.models import DifferentiationFeatures


class DifferentiationScorer:
    def __init__(self, config: DifferentiationConfig | None = None) -> None:
        self.config = config or DifferentiationConfig()

    def score(self, features: DifferentiationFeatures) -> tuple[float, float, float, dict[str, float], dict[str, float]]:
        components = {
            "feature_gap": float(features.feature_gap or 0.0),
            "complaint_gap": float(features.complaint_gap or 0.0),
            "product_depth_gap": float(features.product_depth_gap or 0.0),
            "customization_gap": float(features.customization_gap or 0.0),
            "automation_gap": float(features.automation_gap or 0.0),
            "ux_gap": float(features.ux_gap or 0.0),
            "visual_quality_gap": float(features.visual_quality_gap or 0.0),
            "documentation_gap": float(features.documentation_gap or 0.0),
            "internationalization_gap": float(features.internationalization_gap or 0.0),
            "positioning_gap": float(features.positioning_gap or 0.0),
        }

        weights = self.config.gap_weights
        available = {key: value for key, value in components.items() if value > 0}
        if not available:
            return 0.0, 0.0, 0.0, components, {key: round(value, 4) for key, value in weights.items()}

        weighted_total = sum(value * weights.get(key, 0.0) for key, value in components.items())
        total_weight = sum(weights.get(key, 0.0) for key in components)
        score_value = max(0.0, min(100.0, weighted_total / total_weight if total_weight else 0.0))

        coverage = min(1.0, len(available) / len(components))
        confidence = min(1.0, coverage * 0.7 + 0.3)
        return score_value, confidence, coverage, {key: round(value, 4) for key, value in components.items()}, {key: round(value, 4) for key, value in weights.items()}
