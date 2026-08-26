from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Top10SelectionRepository(ABC):
    @abstractmethod
    def save_run(self, run: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_opportunity(self, item: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_thesis(self, thesis: Any) -> Any:
        raise NotImplementedError


class InMemoryTop10SelectionRepository(Top10SelectionRepository):
    def __init__(self) -> None:
        self.runs: list[Any] = []
        self.opportunities: list[Any] = []
        self.theses: list[Any] = []

    def save_run(self, run: Any) -> Any:
        self.runs.append(run)
        return run

    def save_opportunity(self, item: Any) -> Any:
        self.opportunities.append(item)
        return item

    def save_thesis(self, thesis: Any) -> Any:
        self.theses.append(thesis)
        return thesis
