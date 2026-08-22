from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EligibilityRepository(ABC):
    @abstractmethod
    def save_run(self, run: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save_result(self, result: Any) -> Any:
        raise NotImplementedError
