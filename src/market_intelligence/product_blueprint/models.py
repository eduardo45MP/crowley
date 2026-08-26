from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ProductField:
    name: str
    description: str
    field_type: str = "number"
    required: bool = True
    source: str = "user"


@dataclass(slots=True)
class SheetBlueprint:
    name: str
    purpose: str
    input_fields: list[str] = field(default_factory=list)
    calculated_fields: list[str] = field(default_factory=list)
    output_fields: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    required: bool = True


@dataclass(slots=True)
class FormulaBlueprint:
    name: str
    purpose: str
    inputs: list[str] = field(default_factory=list)
    output: str = "result"
    formula_description: str = ""
    complexity: str = "low"
    assumptions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DashboardBlueprint:
    name: str
    purpose: str
    metrics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkflowBlueprint:
    step: int
    name: str
    description: str
    input_dependencies: list[str] = field(default_factory=list)
    output: str | None = None


@dataclass(slots=True)
class ProductBlueprint:
    cluster_id: int | None
    product_name: str
    product_type: str
    target_buyer: str
    primary_problem: str
    value_proposition: str
    sheets: list[SheetBlueprint] = field(default_factory=list)
    formulas: list[FormulaBlueprint] = field(default_factory=list)
    inputs: list[ProductField] = field(default_factory=list)
    outputs: list[ProductField] = field(default_factory=list)
    dashboards: list[DashboardBlueprint] = field(default_factory=list)
    workflows: list[WorkflowBlueprint] = field(default_factory=list)
    core_features: list[str] = field(default_factory=list)
    differentiation_features: list[str] = field(default_factory=list)
    optional_features: list[str] = field(default_factory=list)
    mvp_features: list[str] = field(default_factory=list)
    post_mvp_features: list[str] = field(default_factory=list)
    configuration_options: list[str] = field(default_factory=list)
    documentation_requirements: list[str] = field(default_factory=list)
    scope_level: str = "small"
    build_complexity: str = "medium"
    estimated_build_hours: float | None = None
    evidence_refs: list[str] = field(default_factory=list)
    blueprint_confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "product_name": self.product_name,
            "product_type": self.product_type,
            "target_buyer": self.target_buyer,
            "primary_problem": self.primary_problem,
            "value_proposition": self.value_proposition,
            "sheets": [sheet.__dict__ for sheet in self.sheets],
            "formulas": [formula.__dict__ for formula in self.formulas],
            "inputs": [field.__dict__ for field in self.inputs],
            "outputs": [field.__dict__ for field in self.outputs],
            "dashboards": [dashboard.__dict__ for dashboard in self.dashboards],
            "workflows": [workflow.__dict__ for workflow in self.workflows],
            "core_features": list(self.core_features),
            "differentiation_features": list(self.differentiation_features),
            "optional_features": list(self.optional_features),
            "mvp_features": list(self.mvp_features),
            "post_mvp_features": list(self.post_mvp_features),
            "configuration_options": list(self.configuration_options),
            "documentation_requirements": list(self.documentation_requirements),
            "scope_level": self.scope_level,
            "build_complexity": self.build_complexity,
            "estimated_build_hours": self.estimated_build_hours,
            "evidence_refs": list(self.evidence_refs),
            "blueprint_confidence": self.blueprint_confidence,
            "warnings": list(self.warnings),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
