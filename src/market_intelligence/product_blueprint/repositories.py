from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProductBlueprintRepository(ABC):
    @abstractmethod
    def save_blueprint(self, blueprint: Any) -> Any:
        raise NotImplementedError


class InMemoryProductBlueprintRepository(ProductBlueprintRepository):
    def __init__(self) -> None:
        self.blueprints: list[Any] = []

    def save_blueprint(self, blueprint: Any) -> Any:
        self.blueprints.append(blueprint)
        return blueprint
