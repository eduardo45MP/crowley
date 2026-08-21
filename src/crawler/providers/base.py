from __future__ import annotations

from abc import ABC, abstractmethod

from crawler.models import Marketplace, RawMarketplaceProduct


class ProviderError(RuntimeError):
    """A marketplace request could not be completed safely."""


class ProviderConfigurationError(ProviderError):
    """A provider is missing credentials or configuration."""


class MarketplaceProvider(ABC):
    marketplace: Marketplace

    @property
    def name(self) -> str:
        return self.marketplace.value

    @abstractmethod
    def search(self, query: str, limit: int) -> list[RawMarketplaceProduct]:
        raise NotImplementedError

