from __future__ import annotations

from market_intelligence.opportunity.config import OpportunityScoreConfig
from market_intelligence.opportunity.models import OpportunityInputs, OpportunityScoreResult


class OpportunityScorer:
    def __init__(self, config: OpportunityScoreConfig | None = None) -> None:
        self.config = config or OpportunityScoreConfig()

    def score(self, inputs: OpportunityInputs) -> OpportunityScoreResult:
        weight_map = self.config.dimension_weights
        ordered = self.config.weighted_order

        available = {}
        for key in ordered:
            value = getattr(inputs, f"{key}_score", None)
            if value is not None:
                available[key] = float(value)

        total_original_weight = sum(weight_map.values())
        available_weight = sum(weight_map[key] for key in available)
        dimension_coverage = available_weight / total_original_weight if total_original_weight else 0.0

        if not available:
            return OpportunityScoreResult(
                cluster_id=inputs.cluster_id,
                opportunity_score=None,
                status="insufficient_data",
                qualification=None,
                opportunity_confidence=None,
                dimension_coverage=0.0,
                evidence_coverage=0.0,
                components={},
                source_analysis_ids={
                    "demand": inputs.demand_analysis_id,
                    "purchase_intent": inputs.purchase_intent_analysis_id,
                    "competition": inputs.competition_analysis_id,
                    "differentiation": inputs.differentiation_analysis_id,
                    "build_ease": inputs.build_ease_analysis_id,
                    "price_potential": inputs.price_potential_analysis_id,
                },
                source_model_versions={
                    "demand": inputs.demand_model_version,
                    "purchase_intent": inputs.purchase_intent_model_version,
                    "competition": inputs.competition_model_version,
                    "differentiation": inputs.differentiation_model_version,
                    "build_ease": inputs.build_ease_model_version,
                    "price_potential": inputs.price_potential_model_version,
                },
                bottlenecks=[],
                strongest_dimension=None,
                weakest_dimension=None,
                fatal_weaknesses=[],
                ranking_eligible=False,
                model_version=self.config.model_version,
                warnings=["no dimensions available"],
            )

        if dimension_coverage < self.config.minimum_dimension_coverage:
            return OpportunityScoreResult(
                cluster_id=inputs.cluster_id,
                opportunity_score=None,
                status="insufficient_data",
                qualification=None,
                opportunity_confidence=None,
                dimension_coverage=dimension_coverage,
                evidence_coverage=self._weighted_evidence(inputs, available, weight_map),
                components={name: float(value) for name, value in available.items()},
                source_analysis_ids={
                    "demand": inputs.demand_analysis_id,
                    "purchase_intent": inputs.purchase_intent_analysis_id,
                    "competition": inputs.competition_analysis_id,
                    "differentiation": inputs.differentiation_analysis_id,
                    "build_ease": inputs.build_ease_analysis_id,
                    "price_potential": inputs.price_potential_analysis_id,
                },
                source_model_versions={
                    "demand": inputs.demand_model_version,
                    "purchase_intent": inputs.purchase_intent_model_version,
                    "competition": inputs.competition_model_version,
                    "differentiation": inputs.differentiation_model_version,
                    "build_ease": inputs.build_ease_model_version,
                    "price_potential": inputs.price_potential_model_version,
                },
                bottlenecks=self._bottlenecks(available, self.config.bottleneck_threshold),
                strongest_dimension=self._strongest_dimension(available),
                weakest_dimension=self._weakest_dimension(available),
                fatal_weaknesses=self._fatal_weaknesses(available),
                ranking_eligible=False,
                model_version=self.config.model_version,
                warnings=["coverage below minimum_dimension_coverage"],
            )

        score = 0.0
        for key in ordered:
            if key not in available:
                continue
            score += (float(getattr(inputs, f"{key}_score")) * weight_map[key])
        score = max(self.config.score_floor, min(self.config.score_ceiling, score / dimension_coverage))

        weighted_evidence = self._weighted_evidence(inputs, available, weight_map)
        opportunity_confidence = self._opportunity_confidence(inputs, available, weight_map)
        bottlenecks = self._bottlenecks(available, self.config.bottleneck_threshold)
        strongest = self._strongest_dimension(available)
        weakest = self._weakest_dimension(available)
        fatal = self._fatal_weaknesses(available)
        status = "complete" if len(available) == len(ordered) else "provisional"
        qualification = self._qualify(score, status, opportunity_confidence, dimension_coverage)
        ranking_eligible = (
            status in {"complete", "provisional"}
            and dimension_coverage >= self.config.minimum_dimension_coverage
            and (opportunity_confidence or 0.0) >= self.config.min_confidence_for_ranking
            and not fatal
        )

        return OpportunityScoreResult(
            cluster_id=inputs.cluster_id,
            opportunity_score=score,
            status=status,
            qualification=qualification,
            opportunity_confidence=opportunity_confidence,
            dimension_coverage=dimension_coverage,
            evidence_coverage=weighted_evidence,
            components={name: float(value) for name, value in available.items()},
            source_analysis_ids={
                "demand": inputs.demand_analysis_id,
                "purchase_intent": inputs.purchase_intent_analysis_id,
                "competition": inputs.competition_analysis_id,
                "differentiation": inputs.differentiation_analysis_id,
                "build_ease": inputs.build_ease_analysis_id,
                "price_potential": inputs.price_potential_analysis_id,
            },
            source_model_versions={
                "demand": inputs.demand_model_version,
                "purchase_intent": inputs.purchase_intent_model_version,
                "competition": inputs.competition_model_version,
                "differentiation": inputs.differentiation_model_version,
                "build_ease": inputs.build_ease_model_version,
                "price_potential": inputs.price_potential_model_version,
            },
            bottlenecks=bottlenecks,
            strongest_dimension=strongest,
            weakest_dimension=weakest,
            fatal_weaknesses=fatal,
            ranking_eligible=ranking_eligible,
            model_version=self.config.model_version,
            warnings=self._warnings(status, opportunity_confidence, fatal),
        )

    @staticmethod
    def _weighted_evidence(inputs: OpportunityInputs, available: dict[str, float], weight_map: dict[str, float]) -> float:
        if not available:
            return 0.0
        weighted = 0.0
        total = 0.0
        for key, weight in weight_map.items():
            value = getattr(inputs, f"{key}_evidence_coverage", None)
            if key not in available or value is None:
                continue
            weighted += float(value) * weight
            total += weight
        if total == 0.0:
            return 0.0
        return max(0.0, min(1.0, weighted / total))

    def _opportunity_confidence(self, inputs: OpportunityInputs, available: dict[str, float], weight_map: dict[str, float]) -> float:
        if not available:
            return 0.0
        total_weight = 0.0
        weighted = 0.0
        for key, weight in weight_map.items():
            if key not in available:
                continue
            confidence = getattr(inputs, f"{key}_confidence", None)
            if confidence is None:
                continue
            weighted += float(confidence) * weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        base = weighted / total_weight
        low_confidence_penalty = 0.0
        for key in ("demand", "purchase_intent"):
            if key in available:
                confidence = getattr(inputs, f"{key}_confidence", None)
                if confidence is not None and float(confidence) < 0.25:
                    low_confidence_penalty += 0.15
        return max(0.0, min(1.0, base - low_confidence_penalty))

    @staticmethod
    def _bottlenecks(available: dict[str, float], threshold: float) -> list[str]:
        return [name for name, value in available.items() if value < threshold]

    @staticmethod
    def _strongest_dimension(available: dict[str, float]) -> str | None:
        if not available:
            return None
        return max(available, key=available.get)

    @staticmethod
    def _weakest_dimension(available: dict[str, float]) -> str | None:
        if not available:
            return None
        return min(available, key=available.get)

    def _fatal_weaknesses(self, available: dict[str, float]) -> list[str]:
        fatal = []
        for key in ("demand", "purchase_intent"):
            value = available.get(key)
            if value is not None and value < self.config.critical_floor:
                fatal.append(key)
        return fatal

    def _qualify(self, score: float, status: str, confidence: float | None, coverage: float) -> str | None:
        if status == "insufficient_data":
            return "insufficient_data"
        if score >= 90 and confidence is not None and confidence >= 0.7 and coverage >= 0.9:
            return "exceptional"
        if score >= 80:
            return "strong"
        if score >= 70:
            return "interesting"
        if score >= 60:
            return "speculative"
        if score >= 0:
            return "weak"
        return None

    @staticmethod
    def _warnings(status: str, confidence: float | None, fatal: list[str]) -> list[str]:
        warnings: list[str] = []
        if status == "provisional":
            warnings.append("provisional score")
        if confidence is not None and confidence < 0.50:
            warnings.append("low confidence")
        if fatal:
            warnings.append("critical weakness")
        return warnings
