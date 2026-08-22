from __future__ import annotations

from abc import ABC, abstractmethod

from market_intelligence.opportunity.models import OpportunityAnalysis, OpportunityInputs


class OpportunityRepository(ABC):
    @abstractmethod
    def load_latest_inputs(self, cluster_id: int) -> OpportunityInputs:
        raise NotImplementedError

    @abstractmethod
    def save_analysis(self, analysis: OpportunityAnalysis) -> OpportunityAnalysis:
        raise NotImplementedError

    @abstractmethod
    def latest_for_cluster(self, cluster_id: int) -> OpportunityAnalysis | None:
        raise NotImplementedError
