from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompetitionConfig:
    target_competitor_count: int = 24
    density_low_count: int = 2
    density_high_count: int = 180
    max_market_saturation: int = 500
    model_version: str = "competition-v1"
    score_floor: float = 0.0
    score_ceiling: float = 100.0
