from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BuildEaseConfig:
    production_complexity_weights: dict[str, float] = field(
        default_factory=lambda: {
            "tabs": 0.25,
            "formula_difficulty": 0.20,
            "api_dependency": 0.20,
            "external_data": 0.15,
            "design_complexity": 0.10,
            "maintenance": 0.10,
        }
    )
    default_max_score: float = 100.0
    model_version: str = "build-ease-v1"
