from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crawler.clustering import ProductCluster
from market_intelligence.eligibility.config import EligibilityConfig
from market_intelligence.eligibility.models import EligibilityRuleResult


@dataclass(slots=True)
class EligibilityContext:
    cluster: ProductCluster
    opportunity_score: float | None = None
    demand_score: float | None = None
    demand_confidence: float | None = None
    competition_score: float | None = None
    differentiation_score: float | None = None
    differentiation_confidence: float | None = None
    build_ease_score: float | None = None
    evidence_coverage: float | None = None
    opportunity_confidence: float | None = None
    source_analysis_ids: dict[str, Any] | None = None
    warnings: list[str] | None = None
    estimated_build_hours: float | None = None


class EligibilityRule:
    rule_id: str = "base_rule"
    severity: str = "warning"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        raise NotImplementedError


class MedicalAdviceRule(EligibilityRule):
    rule_id = "regulated_medical_advice"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        text = " ".join([
            context.cluster.name or "",
            context.cluster.niche or "",
            context.cluster.primary_problem or "",
            *(context.cluster.secondary_problems or []),
            *(context.cluster.keywords or []),
        ]).lower()
        if any(token in text for token in ["diagnosis", "treatment recommendation", "drug dosage", "medical risk", "insulin dose", "medical advice"]):
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="ineligible",
                severity=self.severity,
                observed_value=text,
                threshold="contains regulated medical advice patterns",
                reason="Product targets regulated medical diagnosis or dosing guidance and is outside the supported scope.",
                evidence={"matched_tokens": [token for token in ["diagnosis", "treatment recommendation", "drug dosage", "medical risk", "insulin dose", "medical advice"] if token in text]},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=text,
            threshold="contains regulated medical advice patterns",
            reason="No regulated medical decision-support signal detected.",
            evidence={"matched_tokens": []},
        )


class LegalAdviceRule(EligibilityRule):
    rule_id = "regulated_legal_advice"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        text = " ".join([
            context.cluster.name or "",
            context.cluster.niche or "",
            context.cluster.primary_problem or "",
            *(context.cluster.secondary_problems or []),
            *(context.cluster.keywords or []),
        ]).lower()
        if any(token in text for token in ["lawsuit settlement recommendation", "legal outcome", "legal advice", "case strategy"]):
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="ineligible",
                severity=self.severity,
                observed_value=text,
                threshold="contains regulated legal advice patterns",
                reason="Product aims at legal outcome recommendations or legal strategy and is not eligible for the V1 scope.",
                evidence={"matched_tokens": [token for token in ["lawsuit settlement recommendation", "legal outcome", "legal advice", "case strategy"] if token in text]},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=text,
            threshold="contains regulated legal advice patterns",
            reason="No regulated legal advice pattern detected.",
            evidence={"matched_tokens": []},
        )


class MinimumDemandRule(EligibilityRule):
    rule_id = "minimum_demand"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.demand_score
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity="blocking",
                observed_value=None,
                threshold=config.minimum_demand_score,
                reason="Demand score is missing; cannot validate a minimum-demand gate.",
                evidence={"demand_score": None},
            )
        if value < config.minimum_demand_score:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="ineligible",
                severity=self.severity,
                observed_value=value,
                threshold=config.minimum_demand_score,
                reason="Demand evidence is below the minimum threshold for ranking eligibility.",
                evidence={"demand_score": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.minimum_demand_score,
            reason="Demand score is above the minimum threshold.",
            evidence={"demand_score": value},
        )


class DemandConfidenceRule(EligibilityRule):
    rule_id = "demand_confidence"
    severity = "review"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.demand_confidence
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=None,
                threshold=config.minimum_demand_confidence,
                reason="Demand confidence is missing and cannot be validated.",
                evidence={"demand_confidence": None},
            )
        if value < config.minimum_demand_confidence:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="review_required",
                severity=self.severity,
                observed_value=value,
                threshold=config.minimum_demand_confidence,
                reason="Demand score exists but confidence is too low for a robust eligibility decision.",
                evidence={"demand_confidence": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.minimum_demand_confidence,
            reason="Demand confidence is above the minimum threshold.",
            evidence={"demand_confidence": value},
        )


class ExtremeCompetitionRule(EligibilityRule):
    rule_id = "extreme_competition"
    severity = "review"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.competition_score
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=None,
                threshold=config.minimum_competition_score,
                reason="Competition score is missing; market structure cannot be validated.",
                evidence={"competition_score": None},
            )
        if value < config.minimum_competition_score:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="review_required",
                severity=self.severity,
                observed_value=value,
                threshold=config.minimum_competition_score,
                reason="Competition appears too sparse or too structurally unfavorable for a safe ranking decision.",
                evidence={"competition_score": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.minimum_competition_score,
            reason="Competition score is not indicating a critical structural problem.",
            evidence={"competition_score": value},
        )


class InsufficientDifferentiationRule(EligibilityRule):
    rule_id = "insufficient_differentiation"
    severity = "review"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.differentiation_score
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=None,
                threshold=config.minimum_differentiation_score,
                reason="Differentiation score is missing; differentiability cannot be checked.",
                evidence={"differentiation_score": None},
            )
        confidence = context.differentiation_confidence if context.differentiation_confidence is not None else 0.0
        if value < config.minimum_differentiation_score and confidence >= config.minimum_differentiation_confidence:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="review_required",
                severity=self.severity,
                observed_value=value,
                threshold=config.minimum_differentiation_score,
                reason="Differentiation is extremely weak and confidence is high, suggesting a crowded or non-distinct market.",
                evidence={"differentiation_score": value, "confidence": confidence},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.minimum_differentiation_score,
            reason="Differentiation is not indicating a critical gap problem.",
            evidence={"differentiation_score": value, "confidence": confidence},
        )


class ProductScopeRule(EligibilityRule):
    rule_id = "out_of_scope_product_type"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = (context.cluster.product_type or "").lower()
        if value in config.allowed_product_types:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="pass",
                severity=self.severity,
                observed_value=value,
                threshold=config.allowed_product_types,
                reason="Product type matches the supported V1 scope.",
                evidence={"product_type": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="ineligible",
            severity=self.severity,
            observed_value=value,
            threshold=config.allowed_product_types,
            reason="Product type falls outside the supported V1 product scope.",
            evidence={"product_type": value},
        )


class MisleadingFinancialClaimsRule(EligibilityRule):
    rule_id = "misleading_financial_claims"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        text = " ".join([
            context.cluster.name or "",
            *(context.cluster.keywords or []),
            context.cluster.primary_problem or "",
        ]).lower()
        found = [token for token in config.restricted_keywords if token.lower() in text]
        if found:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="ineligible",
                severity=self.severity,
                observed_value=text,
                threshold="no misleading financial claims",
                reason="Product claims protected outcomes or risk-free returns, which is outside the project scope.",
                evidence={"matched_claims": found},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=text,
            threshold="no misleading financial claims",
            reason="No explicit misleading-financial-claims pattern detected.",
            evidence={"matched_claims": []},
        )


class MinimumEvidenceCoverageRule(EligibilityRule):
    rule_id = "minimum_evidence_coverage"
    severity = "blocking"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.evidence_coverage
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=None,
                threshold=config.minimum_evidence_coverage,
                reason="Evidence coverage is missing; we cannot confirm data sufficiency.",
                evidence={"evidence_coverage": None},
            )
        if value < config.minimum_evidence_coverage:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=value,
                threshold=config.minimum_evidence_coverage,
                reason="Evidence coverage is too low to justify ranking eligibility.",
                evidence={"evidence_coverage": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.minimum_evidence_coverage,
            reason="Evidence coverage exceeds the minimum threshold.",
            evidence={"evidence_coverage": value},
        )


class BuildScopeRule(EligibilityRule):
    rule_id = "max_build_scope"
    severity = "review"

    def evaluate(self, context: EligibilityContext, config: EligibilityConfig) -> EligibilityRuleResult:
        value = context.estimated_build_hours
        if value is None:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="insufficient_data",
                severity=self.severity,
                observed_value=None,
                threshold=config.max_estimated_build_hours,
                reason="Estimated build hours are missing; build scope cannot be validated.",
                evidence={"estimated_build_hours": None},
            )
        if value > config.max_estimated_build_hours:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="ineligible",
                severity=self.severity,
                observed_value=value,
                threshold=config.max_estimated_build_hours,
                reason="Estimated build scope exceeds the supported V1 threshold for micro-products.",
                evidence={"estimated_build_hours": value},
            )
        if value >= config.review_build_hours:
            return EligibilityRuleResult(
                rule_id=self.rule_id,
                status="review_required",
                severity=self.severity,
                observed_value=value,
                threshold=config.review_build_hours,
                reason="Build scope is within range but needs human validation before ranking.",
                evidence={"estimated_build_hours": value},
            )
        return EligibilityRuleResult(
            rule_id=self.rule_id,
            status="pass",
            severity=self.severity,
            observed_value=value,
            threshold=config.max_estimated_build_hours,
            reason="Build scope sits inside the supported project range.",
            evidence={"estimated_build_hours": value},
        )


RULES = [
    MedicalAdviceRule(),
    LegalAdviceRule(),
    MinimumDemandRule(),
    DemandConfidenceRule(),
    ExtremeCompetitionRule(),
    InsufficientDifferentiationRule(),
    ProductScopeRule(),
    MisleadingFinancialClaimsRule(),
    MinimumEvidenceCoverageRule(),
    BuildScopeRule(),
]
