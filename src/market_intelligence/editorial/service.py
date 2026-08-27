from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from market_intelligence.editorial.metrics import (
    PRICING_MODEL_VERSION,
    REVENUE_EFFICIENCY_MODEL_VERSION,
    revenue_efficiency_score,
    summarize_pricing,
)
from market_intelligence.editorial.models import PublishedOpportunity, PublishedReport, ReportSnapshot
from market_intelligence.editorial.positioning import derive_commercial_positioning


EDITORIAL_MODEL_VERSION = "editorial-opportunity-v1"
METHODOLOGY_VERSION = "crowley-methodology-v1"


class EditorialReportService:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def build(
        self,
        *,
        selection_run_id: int | None = None,
        top: int = 100,
        top10_count: int = 10,
        created_at: datetime | None = None,
    ) -> PublishedReport:
        selection_run = self.repository.get_selection_run(selection_run_id) if selection_run_id is not None else self.repository.latest_selection_run()
        if selection_run is None:
            raise ValueError("Nenhuma execução de Selection persistida. Execute `python -m market_intelligence selection run` primeiro.")
        selected = self.repository.list_selected_opportunities(selection_run["id"], limit=max(1, top))
        if not selected:
            raise ValueError(f"A execução de Selection {selection_run['id']} não possui oportunidades persistidas.")

        deep_run = self.repository.latest_deep_research_run(selection_run_id=selection_run["id"])
        dossiers = self.repository.list_deep_research_dossiers(deep_run["id"]) if deep_run else []
        dossier_by_cluster = {item.cluster_id: item for item in dossiers}
        top10_run = self.repository.latest_top10_run(deep_research_run_id=deep_run["id"] if deep_run else None)
        top10_rows = self.repository.list_top10_opportunities(top10_run["id"], limit=max(1, top10_count)) if top10_run else []
        top10_by_cluster = {item["cluster_id"]: item for item in top10_rows}

        ranking: list[PublishedOpportunity] = []
        versions: dict[str, str] = {
            "editorial": EDITORIAL_MODEL_VERSION,
            "pricing": PRICING_MODEL_VERSION,
            "positioning": "editorial-positioning-v1",
            "revenue_efficiency": REVENUE_EFFICIENCY_MODEL_VERSION,
            "selection": selection_run["model_version"],
        }
        if deep_run:
            versions["deep_research"] = deep_run["model_version"]
        if top10_run:
            versions["top10"] = top10_run["model_version"]

        for selected_row in sorted(selected, key=lambda row: row["selection_rank"]):
            cluster_id = int(selected_row["cluster_id"])
            cluster = self.repository.get_cluster_by_id(cluster_id)
            if cluster is None:
                raise ValueError(f"Cluster {cluster_id} referenciado por Selection não foi encontrado.")
            opportunity = self.repository.latest_cluster_opportunity_score(cluster_id) or {}
            components = opportunity.get("components") or {}
            dossier = dossier_by_cluster.get(cluster_id)
            thesis = self.repository.latest_thesis(cluster_id)
            blueprint = self.repository.latest_blueprint(cluster_id)
            top10_row = top10_by_cluster.get(cluster_id)
            pricing = summarize_pricing(getattr(dossier, "pricing_analysis", None))
            positioning = derive_commercial_positioning(
                cluster=cluster,
                buyer_group=selected_row.get("buyer_group"),
                thesis=thesis,
                blueprint=blueprint,
                dossier=dossier,
            )
            keywords = editorial_keywords(cluster, dossier)
            build_hours = _value(blueprint, "estimated_build_hours")
            score = _number(opportunity.get("opportunity_score", selected_row.get("opportunity_score")))
            source_versions = {key: str(value) for key, value in (opportunity.get("source_model_versions") or {}).items() if value}
            item_versions = {
                **source_versions,
                "opportunity": str(opportunity.get("model_version") or "unknown"),
                "selection": str(selection_run["model_version"]),
                "editorial": EDITORIAL_MODEL_VERSION,
                "pricing": PRICING_MODEL_VERSION,
                "positioning": "editorial-positioning-v1",
                "revenue_efficiency": REVENUE_EFFICIENCY_MODEL_VERSION,
            }
            if dossier is not None:
                item_versions["deep_research"] = dossier.model_version
            if top10_row:
                item_versions["top10"] = str(top10_run["model_version"])
            if thesis:
                item_versions["thesis"] = str(thesis.get("model_version") or "opportunity-thesis-v1")
            if blueprint:
                item_versions["product_blueprint"] = str(blueprint.get("model_version") or "product-blueprint-v1")
            versions.update(item_versions)
            warnings = _dedupe([
                *(selected_row.get("warnings") or []),
                *(opportunity.get("warnings") or []),
                *(getattr(dossier, "warnings", []) if dossier else []),
                *(_value(blueprint, "warnings") or []),
            ])
            evidence_refs = build_evidence_refs(
                cluster_id=cluster_id,
                selection_run_id=selection_run["id"],
                opportunity=opportunity,
                dossier=dossier,
                thesis=thesis,
                blueprint=blueprint,
            )
            ranking.append(PublishedOpportunity(
                rank=int(selected_row["selection_rank"]),
                cluster_id=cluster_id,
                product_name=positioning.suggested_product_name or cluster.name,
                product_type=cluster.product_type or selected_row.get("product_type"),
                niche=cluster.niche or selected_row.get("niche"),
                buyer_group=selected_row.get("buyer_group"),
                primary_problem=cluster.primary_problem or selected_row.get("problem_type"),
                demand_score=_number(components.get("demand")),
                competition_score=_number(components.get("competition")),
                purchase_intent_score=_number(components.get("purchase_intent")),
                build_ease_score=_number(components.get("build_ease")),
                differentiation_score=_number(components.get("differentiation")),
                price_potential_score=_number(components.get("price_potential")),
                opportunity_score=score,
                opportunity_confidence=_number(opportunity.get("opportunity_confidence", selected_row.get("opportunity_confidence"))),
                selection_rank=int(selected_row["selection_rank"]),
                top10_rank=int(top10_row["top10_rank"]) if top10_row else None,
                target_buyer=positioning.target_buyer,
                problem=positioning.pain,
                value_proposition=positioning.value_proposition,
                positioning=positioning.short_positioning_statement,
                differentiation=positioning.primary_differentiator,
                price_min=pricing.minimum_observed_price,
                price_median=pricing.median_observed_price,
                price_max=pricing.maximum_observed_price,
                recommended_price=pricing.recommended_price,
                price_currency=pricing.currency,
                keywords=keywords,
                estimated_build_hours=_number(build_hours),
                build_complexity=_value(blueprint, "build_complexity"),
                scope_level=_value(blueprint, "scope_level"),
                revenue_efficiency_score=revenue_efficiency_score(score, _number(build_hours)),
                research_confidence=_number(getattr(dossier, "research_confidence", None)),
                research_coverage=_number(getattr(dossier, "research_coverage", None)),
                thesis=_serializable(thesis),
                blueprint=_serializable(blueprint),
                warnings=warnings,
                evidence_refs=evidence_refs,
                model_versions=dict(sorted(item_versions.items())),
            ))

        ranking.sort(key=lambda item: item.selection_rank or item.rank)
        top10 = sorted((item for item in ranking if item.top10_rank is not None), key=lambda item: item.top10_rank or 999)[:top10_count]
        timestamp = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
        report_id = f"crowley-{timestamp.strftime('%Y%m%dT%H%M%SZ')}-s{selection_run['id']}"
        snapshot = ReportSnapshot(
            report_id=report_id,
            created_at=timestamp,
            application_version=_application_version(),
            database_schema="sqlalchemy-create-all-v1",
            selection_run_id=int(selection_run["id"]),
            deep_research_run_id=int(deep_run["id"]) if deep_run else None,
            top10_run_id=int(top10_run["id"]) if top10_run else None,
            model_versions=dict(sorted(versions.items())),
            opportunity_count=len(ranking),
            top10_count=len(top10),
            requested_opportunity_count=top,
            requested_top10_count=top10_count,
            methodology_version=METHODOLOGY_VERSION,
            observation_metadata=self.repository.observation_metadata([item.cluster_id for item in ranking]),
        )
        methodology = methodology_payload()
        provenance = {
            "trace": "report -> editorial opportunity -> selection/top10 -> opportunity score -> component scores -> cluster -> normalized products -> raw observations",
            "selection_run_id": selection_run["id"],
            "deep_research_run_id": deep_run["id"] if deep_run else None,
            "top10_run_id": top10_run["id"] if top10_run else None,
            "cluster_evidence": {str(item.cluster_id): item.evidence_refs for item in ranking},
        }
        return PublishedReport(snapshot=snapshot, ranking=ranking, top10=top10, methodology=methodology, provenance=provenance)


def editorial_keywords(cluster: Any, dossier: Any | None) -> list[str]:
    values: list[str] = []
    analysis = getattr(dossier, "keyword_analysis", {}) if dossier else {}
    values.extend(analysis.get("top_keywords") or [])
    values.extend(analysis.get("long_tail_keywords") or [])
    for variants in (analysis.get("keyword_variants") or {}).values():
        values.extend(variants or [])
    for intent_terms in (analysis.get("intent_classification") or {}).values():
        values.extend(intent_terms or [])
    values.extend(getattr(cluster, "keywords", []) or [])
    for profile in getattr(dossier, "competitor_profiles", []) if dossier else []:
        values.extend(getattr(profile, "keywords", []) or [])
    return _dedupe(values)


def build_evidence_refs(*, cluster_id: int, selection_run_id: int, opportunity: dict, dossier: Any | None, thesis: Any, blueprint: Any) -> list[str]:
    refs: list[str] = [f"cluster:{cluster_id}", f"selection_run:{selection_run_id}"]
    if opportunity.get("id") is not None:
        refs.append(f"opportunity_score:{opportunity['id']}")
    for name, analysis_id in sorted((opportunity.get("source_analysis_ids") or {}).items()):
        if analysis_id is not None:
            refs.append(f"{name}_analysis:{analysis_id}")
    if dossier is not None:
        if dossier.id is not None:
            refs.append(f"deep_research_dossier:{dossier.id}")
        for profile in dossier.competitor_profiles:
            if profile.url:
                refs.append(profile.url)
    refs.extend(_value(thesis, "evidence_refs") or [])
    refs.extend(_value(blueprint, "evidence_refs") or [])
    return _dedupe(refs)


def methodology_payload() -> dict[str, Any]:
    return {
        "version": METHODOLOGY_VERSION,
        "stages": {
            "demand": "Independent evidence-based demand proxy score.",
            "competition": "Competitive attractiveness score; higher is more favorable.",
            "purchase_intent": "Independent purchase-intent proxy score.",
            "build_ease": "Independent ease-of-construction score.",
            "differentiation": "Evidence-based differentiation potential score.",
            "opportunity_score": "Versioned weighted aggregation of upstream dimensions; it does not represent sales.",
            "eligibility": "Separate acceptance gates for ranking.",
            "selection": "Diversity-aware portfolio selection with quotas and niche/problem limits.",
            "deep_research": "Due diligence that adds context without changing Opportunity Score.",
            "revenue_efficiency": "100 * opportunity / (opportunity + 2 * max(build hours, 1)); comparative only, not a revenue forecast.",
            "recommended_price": "110% of observed median, bounded by observed minimum/maximum; a positioning heuristic, not willingness-to-pay.",
        },
        "limitations": [
            "Reviews are proxies for demand.",
            "Opportunity Score does not represent sales.",
            "Revenue Efficiency is not a revenue forecast.",
            "Marketplace data may be incomplete.",
            "Absence of evidence is not evidence of absence of a market.",
        ],
    }


def _value(value: Any, key: str) -> Any:
    if value is None:
        return None
    return value.get(key) if isinstance(value, dict) else getattr(value, key, None)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _serializable(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if is_dataclass(value):
        return asdict(value)
    return None


def _application_version() -> str:
    try:
        return version("crowley-crawler")
    except PackageNotFoundError:
        return "0.1.0"
