from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class EligibilityRuleResult:
    rule_id: str
    status: str
    severity: str
    observed_value: Any | None = None
    threshold: Any | None = None
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EligibilityResult:
    cluster_id: int | None
    cluster_name: str | None
    status: str
    ranking_eligible: bool
    triggered_rules: list[EligibilityRuleResult] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    review_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = "eligibility-v1"
    id: int | None = None
    run_id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "status": self.status,
            "ranking_eligible": self.ranking_eligible,
            "triggered_rules": [
                {
                    "rule_id": rule.rule_id,
                    "status": rule.status,
                    "severity": rule.severity,
                    "observed_value": rule.observed_value,
                    "threshold": rule.threshold,
                    "reason": rule.reason,
                    "evidence": rule.evidence,
                }
                for rule in self.triggered_rules
            ],
            "blocking_reasons": self.blocking_reasons,
            "review_reasons": self.review_reasons,
            "warnings": self.warnings,
            "evaluated_at": self.evaluated_at.isoformat(),
            "model_version": self.model_version,
        }
