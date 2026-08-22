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
