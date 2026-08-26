from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from market_intelligence.deep_research.models import DeepResearchDossier
from market_intelligence.top10.config import Top10SelectionConfig, default_top10_selection_config
from market_intelligence.top10.models import DeepResearchVerdict, Top10Opportunity, Top10SelectionResult, Top10SelectionRun


class Top10Selector:
    def __init__(self, config: Top10SelectionConfig | None = None) -> None:
        self.config = config or default_top10_selection_config()

    def _determine_verdict(
        self,
        dossier: DeepResearchDossier,
        research_confidence: float,
        evidence_strength: float,
        differentiation_clarity: float,
        thesis_strength: float,
        product_clarity: float,
        contradiction_severity: float,
    ) -> DeepResearchVerdict:
        if dossier.research_coverage < self.config.minimum_research_coverage:
            verdict = "reject"
        elif research_confidence < self.config.minimum_research_confidence:
            verdict = "weakened"
        elif contradiction_severity >= 60:
            verdict = "mixed"
        elif evidence_strength >= 80 and thesis_strength >= 70 and differentiation_clarity >= 70 and product_clarity >= 70:
            verdict = "strong_confirm"
        elif evidence_strength >= 65 and thesis_strength >= 55 and differentiation_clarity >= 55:
            verdict = "confirm"
        elif contradiction_severity >= 30:
            verdict = "mixed"
        elif evidence_strength < 45 or thesis_strength < 40:
            verdict = "weakened"
        else:
            verdict = "confirm"
        return DeepResearchVerdict(
            cluster_id=dossier.cluster_id,
            thesis_strength=thesis_strength,
            evidence_strength=evidence_strength,
            differentiation_clarity=differentiation_clarity,
            product_clarity=product_clarity,
            contradiction_severity=contradiction_severity,
            research_confidence=research_confidence,
            verdict=verdict,
        )

    def _evidence_strength(self, dossier: DeepResearchDossier) -> float:
        coverage = dossier.research_coverage or 0.0
        confidence = dossier.research_confidence or 0.0
        competitor_count = max(0.0, (dossier.competitor_count_analyzed or 0) / 10.0)
        review_signal = 1.0 if (dossier.review_analysis or {}).get("reviews_available") else 0.0
        feature_rows = (dossier.feature_matrix or {}).get("features") or []
        avg_feature_coverage = 0.0
        if feature_rows:
            avg_feature_coverage = sum(float(item.get("coverage_ratio", 0.0)) for item in feature_rows) / len(feature_rows)
        score = 100.0 * (
            0.30 * coverage
            + 0.25 * confidence
            + 0.20 * min(1.0, competitor_count)
            + 0.15 * review_signal
            + 0.10 * avg_feature_coverage
        )
        return max(0.0, min(100.0, score))

    def _thesis_strength(self, dossier: DeepResearchDossier) -> float:
        gap_count = len(dossier.observed_gaps or [])
        pattern_count = len(dossier.market_patterns or [])
        confirmation_count = len(dossier.confirmations or [])
        score = (
            0.30 * min(1.0, gap_count / 4.0)
            + 0.20 * min(1.0, pattern_count / 3.0)
            + 0.30 * min(1.0, confirmation_count / 3.0)
            + 0.20 * float(dossier.research_confidence or 0.0)
        )
        return round(max(0.0, min(100.0, score * 100.0)), 2)

    def _differentiation_clarity(self, dossier: DeepResearchDossier) -> float:
        feature_rows = (dossier.feature_matrix or {}).get("features") or []
        if not feature_rows:
            return 40.0
        average_coverage = sum(float(item.get("coverage_ratio", 0.0)) for item in feature_rows) / len(feature_rows)
        gap_signal = min(1.0, len(dossier.observed_gaps or []) / 4.0)
        score = (0.45 * (1.0 - average_coverage)) + (0.55 * gap_signal)
        return round(max(0.0, min(100.0, score * 100.0)), 2)

    def _product_clarity(self, dossier: DeepResearchDossier) -> float:
        cluster_name = dossier.cluster_name or ""
        keywords = (dossier.keyword_analysis or {}).get("top_keywords") or []
        base = 50.0
        if cluster_name:
            base += 15.0
        if keywords:
            base += 15.0
        if (dossier.product_structure_analysis or {}).get("sheet_names"):
            base += 12.0
        if dossier.observed_gaps:
            base += 8.0
        return round(max(0.0, min(100.0, base)), 2)

    def _contradiction_severity(self, dossier: DeepResearchDossier) -> float:
        severe = 0.0
        severe += min(30.0, 10.0 * len(dossier.contradictions or []))
        severe += min(30.0, 10.0 * len(dossier.warnings or []))
        if (dossier.research_confidence or 0.0) < 0.55:
            severe += 20.0
        if (dossier.research_coverage or 0.0) < 0.5:
            severe += 20.0
        return round(min(100.0, severe), 2)

    def _selection_utility(
        self,
        opportunity_score: float,
        evidence_strength: float,
        differentiation_clarity: float,
        thesis_strength: float,
        product_clarity: float,
        build_ease: float,
        contradiction_severity: float,
    ) -> float:
        weights = self.config.weights
        contradiction_penalty = min(self.config.max_contradiction_penalty, contradiction_severity / 100.0 * self.config.max_contradiction_penalty)
        utility = (
            weights["opportunity_score"] * opportunity_score
            + weights["evidence_strength"] * evidence_strength
            + weights["differentiation_clarity"] * differentiation_clarity
            + weights["thesis_strength"] * thesis_strength
            + weights["product_clarity"] * product_clarity
            + weights["build_ease"] * build_ease
            - contradiction_penalty
        )
        return round(max(0.0, utility), 2)

    def _build_ease_score(self, dossier: DeepResearchDossier, fallback: float | None = None) -> float:
        if fallback is not None:
            return float(fallback)
        structure = (dossier.product_structure_analysis or {})
        sheet_count = len((structure.get("sheet_names") or []))
        if sheet_count <= 3:
            return 80.0
        if sheet_count <= 5:
            return 70.0
        if sheet_count <= 8:
            return 60.0
        return 50.0

    def _redundancy_penalty(self, selected_names: list[str], candidate_name: str | None) -> float:
        if not candidate_name:
            return 0.0
        normalized = candidate_name.lower()
        penalty = 0.0
        for name in selected_names:
            if not name:
                continue
            if normalized == name.lower():
                penalty += self.config.redundancy_penalty
            else:
                overlap = len(set(normalized.split()) & set(name.lower().split()))
                if overlap and overlap >= 2:
                    penalty += self.config.redundancy_penalty * 0.5
        return penalty

    def _candidate_sort_key(self, candidate: dict[str, Any]) -> tuple[float, float, float, int | None]:
        return (
            float(candidate.get("top10_selection_utility", 0.0)),
            float(candidate.get("opportunity_score", 0.0)),
            float(candidate.get("research_confidence", 0.0)),
            int(candidate.get("cluster_id") or -1),
        )

    def select(
        self,
        dossiers: list[DeepResearchDossier],
        opportunity_scores: dict[int | None, float] | None = None,
        build_ease_scores: dict[int | None, float] | None = None,
    ) -> Top10SelectionResult:
        started_at = datetime.now(timezone.utc)
        candidate_scores: list[dict[str, Any]] = []
        opportunity_scores = opportunity_scores or {}
        build_ease_scores = build_ease_scores or {}
        selected_names: list[str] = []

        for dossier in dossiers:
            research_confidence = float(dossier.research_confidence or 0.0)
            evidence_strength = self._evidence_strength(dossier)
            differentiation_clarity = self._differentiation_clarity(dossier)
            thesis_strength = self._thesis_strength(dossier)
            product_clarity = self._product_clarity(dossier)
            contradiction_severity = self._contradiction_severity(dossier)
            verdict = self._determine_verdict(
                dossier,
                research_confidence,
                evidence_strength,
                differentiation_clarity,
                thesis_strength,
                product_clarity,
                contradiction_severity,
            )
            opportunity_score = float(opportunity_scores.get(dossier.cluster_id, 0.0) or 0.0)
            build_ease = self._build_ease_score(dossier, build_ease_scores.get(dossier.cluster_id))
            utility = self._selection_utility(
                opportunity_score,
                evidence_strength,
                differentiation_clarity,
                thesis_strength,
                product_clarity,
                build_ease,
                contradiction_severity,
            )

            if dossier.research_coverage < self.config.minimum_research_coverage:
                verdict.verdict = "reject"
            if verdict.verdict in {"reject", "weakened"}:
                utility -= 20.0

            candidate_scores.append(
                {
                    "cluster_id": dossier.cluster_id,
                    "cluster_name": dossier.cluster_name,
                    "opportunity_score": opportunity_score,
                    "dossier": dossier,
                    "deep_research_verdict": verdict,
                    "research_confidence": research_confidence,
                    "top10_selection_utility": utility,
                    "evidence_strength": evidence_strength,
                    "differentiation_clarity": differentiation_clarity,
                    "thesis_strength": thesis_strength,
                    "product_clarity": product_clarity,
                    "build_ease": build_ease,
                    "contradiction_severity": contradiction_severity,
                }
            )

        ranked = sorted(candidate_scores, key=self._candidate_sort_key, reverse=True)
        selected: list[Top10Opportunity] = []
        rejected: list[DeepResearchVerdict] = []

        for candidate in ranked:
            verdict = candidate["deep_research_verdict"]
            if verdict.verdict == "reject":
                rejected.append(verdict)
                continue
            if candidate["research_confidence"] < self.config.minimum_research_confidence:
                rejected.append(verdict)
                continue
            redundancy_penalty = self._redundancy_penalty(selected_names, candidate["cluster_name"])
            adjusted_utility = candidate["top10_selection_utility"] - redundancy_penalty
            if adjusted_utility < 0:
                rejected.append(verdict)
                continue
            selected_names.append(candidate["cluster_name"] or "")
            selected.append(
                Top10Opportunity(
                    cluster_id=candidate["cluster_id"],
                    cluster_name=candidate["cluster_name"],
                    top10_rank=len(selected) + 1,
                    opportunity_score=candidate["opportunity_score"],
                    top10_selection_utility=adjusted_utility,
                    deep_research_verdict=verdict.verdict,
                    research_confidence=candidate["research_confidence"],
                    selection_reasons=[
                        f"Opportunity score {candidate['opportunity_score']:.2f}",
                        f"Evidence strength {candidate['evidence_strength']:.1f}/100",
                        f"Differentiation clarity {candidate['differentiation_clarity']:.1f}/100",
                    ],
                    warnings=list(candidate["dossier"].warnings or []),
                )
            )
            if len(selected) >= self.config.target_size:
                break

        for candidate in ranked:
            verdict = candidate["deep_research_verdict"]
            if not any(item.cluster_id == verdict.cluster_id for item in selected) and verdict.verdict != "reject":
                rejected.append(verdict)

        run = Top10SelectionRun(
            model_version=self.config.model_version,
            configuration={
                "target_size": self.config.target_size,
                "minimum_research_coverage": self.config.minimum_research_coverage,
                "minimum_research_confidence": self.config.minimum_research_confidence,
                "weights": self.config.weights,
            },
            candidate_count=len(ranked),
            selected_count=len(selected),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

        diagnostics = {
            "average_top10_utility": round(sum(float(item.top10_selection_utility or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "average_opportunity_score": round(sum(float(item.opportunity_score or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "average_research_confidence": round(sum(float(item.research_confidence or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "selection_count": len(selected),
            "rejected_count": len(rejected),
        }
        return Top10SelectionResult(run=run, selected=selected, rejected=rejected, diagnostics=diagnostics)

    def run(
        self,
        dossiers: list[DeepResearchDossier],
        opportunity_scores: dict[int | None, float] | None = None,
        build_ease_scores: dict[int | None, float] | None = None,
    ) -> Top10SelectionResult:
        return self.select(dossiers, opportunity_scores=opportunity_scores, build_ease_scores=build_ease_scores)
