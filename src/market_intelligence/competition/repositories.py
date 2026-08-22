from __future__ import annotations

from abc import ABC, abstractmethod

from crawler.clustering import ProductCluster
from market_intelligence.competition.models import ClusterCompetitionScore, CompetitionAnalysisRun


class CompetitionRepository(ABC):
    @abstractmethod
    def create_run(self, run: CompetitionAnalysisRun) -> CompetitionAnalysisRun:
        raise NotImplementedError

    @abstractmethod
    def save_score(self, score: ClusterCompetitionScore) -> ClusterCompetitionScore:
        raise NotImplementedError

    @abstractmethod
    def latest_for_cluster(self, cluster_id: int) -> ClusterCompetitionScore | None:
        raise NotImplementedError

    @abstractmethod
    def list_top_scores(self, limit: int = 20) -> list[ClusterCompetitionScore]:
        raise NotImplementedError
