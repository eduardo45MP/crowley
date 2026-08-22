from __future__ import annotations

from market_intelligence.build_ease.config import BuildEaseConfig
from market_intelligence.build_ease.models import BuildEaseFeatures


class BuildEaseScorer:
    def __init__(self, config: BuildEaseConfig | None = None) -> None:
        self.config = config or BuildEaseConfig()

    def score(self, features: BuildEaseFeatures) -> tuple[float, float, float, dict[str, float], dict[str, float]]:
        components = {
            "tabs": float(features.tab_count or 0.0),
            "formula_difficulty": float(features.formula_difficulty or 0.0),
            "api_dependency": float(features.api_dependency or 0.0),
            "external_data": float(features.external_data_need or 0.0),
            "design_complexity": float(features.design_complexity or 0.0),
            "maintenance": float(features.maintenance_need or 0.0),
        }

        weights = self.config.production_complexity_weights
        weighted_total = sum((value * weights[key]) for key, value in components.items())
        total_weight = sum(weights.values())
        complexity_index = max(0.0, min(100.0, (weighted_total / total_weight)))

        build_ease_score = max(0.0, min(100.0, 100.0 - complexity_index))
        coverage = min(1.0, len([value for value in components.values() if value > 0]) / len(components))
        confidence = min(1.0, coverage * 0.7 + 0.3)

        return build_ease_score, confidence, coverage, {key: round(value, 4) for key, value in components.items()}, {key: round(value, 4) for key, value in weights.items()}
