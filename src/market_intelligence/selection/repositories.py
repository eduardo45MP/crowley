from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SelectionRepository(ABC):
    @abstractmethod
    def save_run(self, run: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_selected_opportunity(self, item: Any) -> Any:
        raise NotImplementedError
