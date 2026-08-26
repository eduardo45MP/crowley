from __future__ import annotations

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DeepResearchRepository(ABC):
    @abstractmethod
    def save_run(self, run: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_dossier(self, dossier: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_competitor_profile(self, profile: Any, run_id: int | None = None) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_evidence(self, evidence: Any, dossier_id: int | None = None) -> Any:
        raise NotImplementedError


class InMemoryDeepResearchRepository(DeepResearchRepository):
    def __init__(self) -> None:
        self.runs: list[Any] = []
        self.dossiers: list[Any] = []
        self.competitor_profiles: list[Any] = []
        self.evidence: list[Any] = []

    def save_run(self, run: Any) -> Any:
        self.runs.append(run)
        return run

    def save_dossier(self, dossier: Any) -> Any:
        self.dossiers.append(dossier)
        return dossier

    def save_competitor_profile(self, profile: Any, run_id: int | None = None) -> Any:
        self.competitor_profiles.append({"run_id": run_id, "profile": profile})
        return profile

    def save_evidence(self, evidence: Any, dossier_id: int | None = None) -> Any:
        self.evidence.append({"dossier_id": dossier_id, "evidence": evidence})
        return evidence
