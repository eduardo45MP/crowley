from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from crawler.models import SearchResult


class ResultStore(ABC):
    @abstractmethod
    def save(self, result: SearchResult) -> Path:
        raise NotImplementedError

