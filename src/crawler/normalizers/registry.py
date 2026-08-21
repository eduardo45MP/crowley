from __future__ import annotations

from crawler.models import Marketplace
from crawler.normalizers.base import NormalizationError, ProductNormalizer
from crawler.normalizers.etsy import EtsyProductNormalizer
from crawler.normalizers.mock import MockProductNormalizer


class ProductNormalizerRegistry:
    def __init__(self) -> None:
        self._normalizers: dict[Marketplace, ProductNormalizer] = {}

    def register(self, marketplace: Marketplace, normalizer: ProductNormalizer) -> None:
        self._normalizers[marketplace] = normalizer

    def get(self, marketplace: Marketplace) -> ProductNormalizer:
        try:
            return self._normalizers[marketplace]
        except KeyError as exc:
            raise NormalizationError(f"Normalizer não registrado para {marketplace.value}") from exc


def default_normalizer_registry() -> ProductNormalizerRegistry:
    registry = ProductNormalizerRegistry()
    registry.register(Marketplace.ETSY, EtsyProductNormalizer())
    registry.register(Marketplace.MOCK, MockProductNormalizer())
    return registry
