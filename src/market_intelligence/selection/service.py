from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import ceil

from market_intelligence.selection.config import SelectionPolicy
from market_intelligence.selection.models import OpportunityCandidate, SelectedOpportunity, SelectionResult, SelectionRun
from market_intelligence.selection.optimizer import selection_utility


@dataclass(slots=True)
class PortfolioSelector:
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    model_version: str = "selection-v1"

    @staticmethod
    def _normalize_group(candidate: OpportunityCandidate) -> str:
        return (candidate.buyer_group or "other").strip() or "other"

    @staticmethod
    def _is_candidate_eligible(candidate: OpportunityCandidate, minimum_score: float, minimum_confidence: float, minimum_evidence: float) -> bool:
        return (
            bool(candidate.ranking_eligible)
            and (candidate.opportunity_score or 0.0) >= minimum_score
            and (candidate.opportunity_confidence or 0.0) >= minimum_confidence
            and (candidate.evidence_coverage or 0.0) >= minimum_evidence
        )

    @staticmethod
    def _candidate_key(candidate: OpportunityCandidate) -> tuple[float, float, float, int | None]:
        return (
            float(candidate.opportunity_score or 0.0),
            float(candidate.opportunity_confidence or 0.0),
            float(candidate.evidence_coverage or 0.0),
            candidate.cluster_id if candidate.cluster_id is not None else -1,
        )

    def _within_portfolio_limits(
        self,
        candidate: OpportunityCandidate,
        category_counts: dict[str, int],
        niche_counts: dict[str, int],
        problem_counts: dict[str, int],
        policy: SelectionPolicy,
    ) -> bool:
        group = self._normalize_group(candidate)
        quota = policy.buyer_group_quotas.get(group)
        if quota is not None and category_counts.get(group, 0) >= quota.get("maximum", policy.target_size):
            return False
        if niche_counts.get(candidate.niche or "unknown", 0) >= policy.max_per_niche:
            return False
        problem_limit = max(policy.max_per_niche, ceil(policy.target_size * policy.max_problem_share))
        if problem_counts.get(candidate.problem_type or "unknown", 0) >= problem_limit:
            return False
        return True

    def _append_selected(
        self,
        selected: list[SelectedOpportunity],
        selected_ids: set[int | None],
        candidate: OpportunityCandidate,
        group: str,
        quota_bucket: str,
        reason: str,
        category_counts: dict[str, int],
        niche_counts: dict[str, int],
        problem_counts: dict[str, int],
    ) -> None:
        selected_ids.add(candidate.cluster_id)
        candidate.selection_utility = selection_utility(candidate, [
            OpportunityCandidate(
                cluster_id=item.cluster_id,
                cluster_name=item.cluster_name,
                opportunity_score=item.opportunity_score,
                opportunity_confidence=item.opportunity_confidence,
                evidence_coverage=item.evidence_coverage,
                buyer_group=item.buyer_group,
                niche=item.niche,
                problem_type=item.problem_type,
                product_type=item.product_type,
                ranking_eligible=True,
            )
            for item in selected
        ])
        selected.append(
            SelectedOpportunity(
                cluster_id=candidate.cluster_id,
                cluster_name=candidate.cluster_name,
                selection_rank=len(selected) + 1,
                buyer_group=self._normalize_group(candidate),
                quota_bucket=quota_bucket,
                niche=candidate.niche,
                problem_type=candidate.problem_type,
                product_type=candidate.product_type,
                opportunity_score=candidate.opportunity_score,
                opportunity_confidence=candidate.opportunity_confidence,
                evidence_coverage=candidate.evidence_coverage,
                selection_utility=candidate.selection_utility,
                selection_reasons=[reason],
            )
        )
        category_counts[group] += 1
        niche_counts[candidate.niche or "unknown"] += 1
        problem_counts[candidate.problem_type or "unknown"] += 1

    def _best_next_candidate(
        self,
        ranked: list[OpportunityCandidate],
        selected_ids: set[int | None],
        group: str | None,
        category_counts: dict[str, int],
        niche_counts: dict[str, int],
        max_per_niche: int,
    ) -> OpportunityCandidate | None:
        best: OpportunityCandidate | None = None
        best_utility = float("-inf")
        for candidate in ranked:
            if candidate.cluster_id in selected_ids:
                continue
            candidate_group = self._normalize_group(candidate)
            if group is not None and candidate_group != group:
                continue
            if niche_counts.get(candidate.niche or "unknown", 0) >= max_per_niche:
                continue
            utility = selection_utility(candidate, [
                OpportunityCandidate(
                    cluster_id=item.cluster_id,
                    cluster_name=item.cluster_name,
                    opportunity_score=item.opportunity_score,
                    opportunity_confidence=item.opportunity_confidence,
                    evidence_coverage=item.evidence_coverage,
                    buyer_group=item.buyer_group,
                    niche=item.niche,
                    problem_type=item.problem_type,
                    product_type=item.product_type,
                    ranking_eligible=True,
                )
                for item in selected_ids if False
            ])
            if utility > best_utility:
                best_utility = utility
                best = candidate
        return best

    def select(self, candidates: list[OpportunityCandidate], policy: SelectionPolicy | None = None) -> SelectionResult:
        effective_policy = policy or self.policy
        started_at = datetime.now(timezone.utc)
        eligible = [candidate for candidate in candidates if candidate.ranking_eligible is True]
        filtered = [
            candidate
            for candidate in eligible
            if self._is_candidate_eligible(
                candidate,
                effective_policy.minimum_opportunity_score,
                effective_policy.minimum_confidence,
                effective_policy.minimum_evidence_coverage,
            )
        ]
        ranked = sorted(filtered, key=self._candidate_key, reverse=True)

        selected: list[SelectedOpportunity] = []
        selected_ids: set[int | None] = set()
        category_counts: dict[str, int] = defaultdict(int)
        niche_counts: dict[str, int] = defaultdict(int)
        problem_counts: dict[str, int] = defaultdict(int)

        for group, quota in effective_policy.buyer_group_quotas.items():
            if len(selected) >= effective_policy.target_size:
                break
            group_candidates = [candidate for candidate in ranked if self._normalize_group(candidate) == group]
            minimum_slots = min(quota["minimum"], max(0, effective_policy.target_size - len(selected)))
            for _ in range(minimum_slots):
                if len(selected) >= effective_policy.target_size:
                    break
                chosen = None
                chosen_score = float("-inf")
                for candidate in group_candidates:
                    if candidate.cluster_id in selected_ids:
                        continue
                    if not self._within_portfolio_limits(candidate, category_counts, niche_counts, problem_counts, effective_policy):
                        continue
                    candidate_score = selection_utility(candidate, [
                        OpportunityCandidate(
                            cluster_id=item.cluster_id,
                            cluster_name=item.cluster_name,
                            opportunity_score=item.opportunity_score,
                            opportunity_confidence=item.opportunity_confidence,
                            evidence_coverage=item.evidence_coverage,
                            buyer_group=item.buyer_group,
                            niche=item.niche,
                            problem_type=item.problem_type,
                            product_type=item.product_type,
                            ranking_eligible=True,
                        )
                        for item in selected
                    ])
                    if candidate_score > chosen_score:
                        chosen = candidate
                        chosen_score = candidate_score
                if chosen is None:
                    break
                self._append_selected(selected, selected_ids, chosen, group, group, "minimum quota", category_counts, niche_counts, problem_counts)

        for group, quota in effective_policy.buyer_group_quotas.items():
            while category_counts.get(group, 0) < quota["target"] and len(selected) < effective_policy.target_size:
                chosen = None
                chosen_score = float("-inf")
                for candidate in ranked:
                    if candidate.cluster_id in selected_ids:
                        continue
                    if self._normalize_group(candidate) != group:
                        continue
                    if not self._within_portfolio_limits(candidate, category_counts, niche_counts, problem_counts, effective_policy):
                        continue
                    utility = selection_utility(candidate, [
                        OpportunityCandidate(
                            cluster_id=item.cluster_id,
                            cluster_name=item.cluster_name,
                            opportunity_score=item.opportunity_score,
                            opportunity_confidence=item.opportunity_confidence,
                            evidence_coverage=item.evidence_coverage,
                            buyer_group=item.buyer_group,
                            niche=item.niche,
                            problem_type=item.problem_type,
                            product_type=item.product_type,
                            ranking_eligible=True,
                        )
                        for item in selected
                    ])
                    if utility > chosen_score:
                        chosen = candidate
                        chosen_score = utility
                if chosen is None:
                    break
                self._append_selected(selected, selected_ids, chosen, group, group, "target quota", category_counts, niche_counts, problem_counts)

        while len(selected) < effective_policy.target_size:
            chosen = None
            chosen_score = float("-inf")
            for candidate in ranked:
                if candidate.cluster_id in selected_ids:
                    continue
                if not self._within_portfolio_limits(candidate, category_counts, niche_counts, problem_counts, effective_policy):
                    continue
                utility = selection_utility(candidate, [
                    OpportunityCandidate(
                        cluster_id=item.cluster_id,
                        cluster_name=item.cluster_name,
                        opportunity_score=item.opportunity_score,
                        opportunity_confidence=item.opportunity_confidence,
                        evidence_coverage=item.evidence_coverage,
                        buyer_group=item.buyer_group,
                        niche=item.niche,
                        problem_type=item.problem_type,
                        product_type=item.product_type,
                        ranking_eligible=True,
                    )
                    for item in selected
                ])
                if utility > chosen_score:
                    chosen = candidate
                    chosen_score = utility
            if chosen is None:
                break
            self._append_selected(
                selected,
                selected_ids,
                chosen,
                self._normalize_group(chosen),
                self._normalize_group(chosen),
                "portfolio diversification",
                category_counts,
                niche_counts,
                problem_counts,
            )

        run = SelectionRun(
            model_version=self.model_version,
            configuration={
                "target_size": effective_policy.target_size,
                "minimum_opportunity_score": effective_policy.minimum_opportunity_score,
                "minimum_confidence": effective_policy.minimum_confidence,
                "minimum_evidence_coverage": effective_policy.minimum_evidence_coverage,
                "quotas": effective_policy.buyer_group_quotas,
            },
            candidate_count=len(candidates),
            eligible_count=len(eligible),
            selected_count=len(selected),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

        diagnostics = {
            "average_opportunity_score": round(sum(float(item.opportunity_score or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "average_confidence": round(sum(float(item.opportunity_confidence or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "average_evidence_coverage": round(sum(float(item.evidence_coverage or 0.0) for item in selected) / len(selected), 2) if selected else 0.0,
            "portfolio_distribution": dict(sorted(category_counts.items())),
            "niche_counts": dict(sorted(niche_counts.items())),
            "problem_counts": dict(sorted(problem_counts.items())),
            "eligible_candidates": len(eligible),
            "filtered_candidates": len(filtered),
        }

        return SelectionResult(
            run=run,
            selected=selected,
            rejected=[candidate for candidate in ranked if candidate.cluster_id not in selected_ids],
            portfolio_distribution=dict(sorted(category_counts.items())),
            diagnostics=diagnostics,
        )

    def run(self, candidates: list[OpportunityCandidate], policy: SelectionPolicy | None = None) -> SelectionResult:
        return self.select(candidates, policy=policy)
