from __future__ import annotations

from datetime import datetime, timezone

from market_intelligence.deep_research.models import DeepResearchDossier
from market_intelligence.top10.models import OpportunityThesis


class OpportunityThesisService:
    def __init__(self) -> None:
        self.model_version = "opportunity-thesis-v1"

    def build(self, cluster: object, dossier: DeepResearchDossier, opportunity_score: float | None = None) -> OpportunityThesis:
        cluster_name = getattr(cluster, "name", None) or getattr(dossier, "cluster_name", None) or "Opportunity"
        cluster_id = getattr(cluster, "id", None) or getattr(dossier, "cluster_id", None)
        niche = getattr(cluster, "niche", None) or "general"
        problem = getattr(cluster, "primary_problem", None) or (dossier.observed_gaps[0] if dossier.observed_gaps else "pricing and workflow pain")
        target_buyer = niche.replace("_", " ")
        evidence = [
            item for item in (dossier.confirmations or [])
        ]
        if not evidence:
            evidence = ["The cluster shows recurring product-market signals across benchmark listings."]
        buyer_evidence = [
            item for item in (dossier.review_analysis or {}).get("complaint_themes", [])
        ]
        if not buyer_evidence:
            buyer_evidence = ["Buyer complaints point to practical workflow and cost-calculation pain points."]
        competitor_weaknesses = list(dossier.observed_gaps or [])
        if not competitor_weaknesses:
            competitor_weaknesses = ["Current market offerings do not fully cover key workflow and cost assumptions."]
        critical_gaps = list(dossier.observed_gaps or [])
        if not critical_gaps:
            critical_gaps = ["labor, waste, and packaging are under-covered relative to the user problem."]
        proposed_advantage = list(dossier.differentiation_axes or [])
        if not proposed_advantage:
            proposed_advantage = ["Clearer cost logic and stronger workflow simplicity."]

        evidence_refs = [
            f"research_confidence={dossier.research_confidence}",
            f"coverage={dossier.research_coverage}",
            *(dossier.market_patterns or [])[:3],
        ]
        statement = (
            f"There is strong evidence of demand for {cluster_name}, especially among {target_buyer} buyers. "
            f"Current competitors commonly {critical_gaps[0] if critical_gaps else 'leave key workflow assumptions underspecified'}. "
            f"A differentiated product could improve this by {proposed_advantage[0] if proposed_advantage else 'simplifying the user workflow and improving cost transparency'}."
        )
        confidence = min(1.0, max(0.0, (dossier.research_confidence or 0.0) * 0.7 + (0.3 if evidence else 0.0)))
        return OpportunityThesis(
            cluster_id=cluster_id,
            target_buyer=target_buyer,
            problem=str(problem),
            market_evidence=evidence,
            buyer_evidence=buyer_evidence,
            competitor_weaknesses=competitor_weaknesses,
            critical_gaps=critical_gaps,
            proposed_advantage=proposed_advantage,
            opportunity_statement=statement,
            evidence_refs=evidence_refs,
            confidence=round(confidence, 4),
            created_at=datetime.now(timezone.utc),
        )

    def create(self, cluster: object, dossier: DeepResearchDossier, opportunity_score: float | None = None) -> OpportunityThesis:
        return self.build(cluster, dossier, opportunity_score=opportunity_score)
