from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from crawler.clustering import ProductCluster
from market_intelligence.eligibility.config import EligibilityConfig
from market_intelligence.eligibility.models import EligibilityResult, EligibilityRuleResult
from market_intelligence.eligibility.rules import EligibilityContext, RULES
from market_intelligence.opportunity.models import OpportunityAnalysis


@dataclass(slots=True)
class EligibilityService:
    config: EligibilityConfig = EligibilityConfig()
    model_version: str = "eligibility-v1"

    def evaluate_cluster(
        self,
        cluster: ProductCluster,
        opportunity: OpportunityAnalysis | None = None,
        demand_score: float | None = None,
        demand_confidence: float | None = None,
        competition_score: float | None = None,
        differentiation_score: float | None = None,
        differentiation_confidence: float | None = None,
        evidence_coverage: float | None = None,
        build_ease_score: float | None = None,
        estimated_build_hours: float | None = None,
    ) -> EligibilityResult:
        context = EligibilityContext(
            cluster=cluster,
            opportunity_score=opportunity.opportunity_score if opportunity is not None else None,
            demand_score=demand_score if demand_score is not None else getattr(opportunity, "components", {}).get("demand") if opportunity is not None else None,
            demand_confidence=demand_confidence if demand_confidence is not None else (0.0 if opportunity is None else 0.75),
            competition_score=competition_score if competition_score is not None else (getattr(opportunity, "components", {}).get("competition") if opportunity is not None else None),
            differentiation_score=differentiation_score if differentiation_score is not None else (getattr(opportunity, "components", {}).get("differentiation") if opportunity is not None else None),
            differentiation_confidence=differentiation_confidence if differentiation_confidence is not None else 0.7,
            build_ease_score=build_ease_score if build_ease_score is not None else (getattr(opportunity, "components", {}).get("build_ease") if opportunity is not None else None),
            evidence_coverage=evidence_coverage if evidence_coverage is not None else (opportunity.evidence_coverage if opportunity is not None else None),
            opportunity_confidence=opportunity.opportunity_confidence if opportunity is not None else None,
            source_analysis_ids=getattr(opportunity, "source_analysis_ids", None),
            warnings=getattr(opportunity, "warnings", None),
            estimated_build_hours=estimated_build_hours,
        )

        results: list[EligibilityRuleResult] = []
        for rule in RULES:
            result = rule.evaluate(context, self.config)
            if result.status != "pass":
                results.append(result)

        blocking = [rule.rule_id for rule in results if rule.status == "ineligible" and rule.severity == "blocking"]
        review = [rule.rule_id for rule in results if rule.status == "review_required" and rule.severity == "review"]
        insufficient = [rule.rule_id for rule in results if rule.status == "insufficient_data"]
        warnings = [rule.reason for rule in results if rule.severity == "warning"]

        if blocking:
            final_status = "ineligible"
            ranking_eligible = False
        elif review:
            final_status = "review_required"
            ranking_eligible = False
        elif insufficient:
            final_status = "insufficient_data"
            ranking_eligible = False
        else:
            final_status = "eligible"
            ranking_eligible = True

        allowed_warnings = list(getattr(context, "warnings", None) or [])
        blocking_reasons = [rule.rule_id for rule in results if rule.status == "ineligible" and rule.severity == "blocking"]
        review_reasons = [rule.rule_id for rule in results if rule.status == "review_required"]
        if final_status == "ineligible" and not blocking_reasons:
            blocking_reasons = ["eligibility_policy_exception"]
        if final_status == "insufficient_data":
            review_reasons = list(insufficient)

        return EligibilityResult(
            cluster_id=getattr(cluster, "id", None),
            cluster_name=getattr(cluster, "name", None),
            status=final_status,
            ranking_eligible=ranking_eligible,
            triggered_rules=results,
            blocking_reasons=blocking_reasons,
            review_reasons=review_reasons,
            warnings=allowed_warnings + warnings,
            evaluated_at=datetime.now(timezone.utc),
            model_version=self.model_version,
        )

    def evaluate(self, cluster: ProductCluster, opportunity: OpportunityAnalysis | None = None, **kwargs: Any) -> EligibilityResult:
        return self.evaluate_cluster(cluster, opportunity=opportunity, **kwargs)
