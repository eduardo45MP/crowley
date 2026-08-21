from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crawler.config import CrawlerConfig
from crawler.models import Marketplace, RawMarketplaceProduct
from crawler.providers.base import MarketplaceProvider, ProviderConfigurationError, ProviderError

logger = logging.getLogger(__name__)


class EtsyProvider(MarketplaceProvider):
    """Etsy Open API v3 collector; it preserves response items without normalizing them."""

    marketplace = Marketplace.ETSY
    endpoint = "https://api.etsy.com/v3/application/listings/active"

    def __init__(
        self,
        config: CrawlerConfig,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.api_key = api_key or os.getenv("ETSY_API_KEY")
        self.api_secret = api_secret or os.getenv("ETSY_API_SECRET")
        self._opener = opener
        self._sleep = sleeper
        self._last_request_at: float | None = None

    def search(self, query: str, limit: int) -> list[RawMarketplaceProduct]:
        if not self.api_key or not self.api_secret:
            raise ProviderConfigurationError(
                "Etsy requer ETSY_API_KEY e ETSY_API_SECRET de uma aplicação aprovada. "
                "Use --provider mock enquanto as credenciais não estiverem disponíveis."
            )
        raw_products: list[RawMarketplaceProduct] = []
        offset = 0
        while len(raw_products) < limit:
            page_size = min(100, limit - len(raw_products))
            payload = self._request(
                {"keywords": query, "limit": page_size, "offset": offset, "sort_on": "score"}
            )
            results = payload.get("results")
            if not isinstance(results, list):
                raise ProviderError("Resposta inválida da Etsy: o campo 'results' não é uma lista.")
            collected_at = datetime.now(timezone.utc)
            for item in results:
                if not isinstance(item, dict):
                    logger.warning("Listing Etsy ignorada: item raw não é um objeto")
                    continue
                external_id = item.get("listing_id")
                raw_products.append(
                    RawMarketplaceProduct(
                        marketplace=self.marketplace,
                        external_id=str(external_id) if external_id is not None else None,
                        query=query,
                        raw_payload=item,
                        collected_at=collected_at,
                    )
                )
            if len(results) < page_size:
                break
            offset += len(results)
        return raw_products[:limit]

    def _request(self, params: dict[str, object]) -> dict[str, Any]:
        url = f"{self.endpoint}?{urlencode(params)}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "crowley-crawler/0.2",
            "x-api-key": f"{self.api_key}:{self.api_secret}",
        }
        for attempt in range(self.config.max_retries + 1):
            self._throttle()
            try:
                request = Request(url, headers=headers)
                with self._opener(request, timeout=self.config.timeout) as response:
                    body = response.read().decode("utf-8")
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise ProviderError("Resposta inválida da Etsy: JSON raiz não é um objeto.")
                return payload
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= self.config.max_retries:
                    raise ProviderError(f"Etsy respondeu com HTTP {exc.code}.") from exc
                delay = self._retry_delay(attempt, exc.headers.get("Retry-After"))
            except (URLError, TimeoutError) as exc:
                if attempt >= self.config.max_retries:
                    raise ProviderError(f"Falha ao acessar a Etsy: {exc}.") from exc
                delay = self._retry_delay(attempt)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ProviderError("A Etsy retornou uma resposta que não é JSON válido.") from exc
            logger.warning("Tentativa Etsy %s falhou; novo envio em %.1fs", attempt + 1, delay)
            self._sleep(delay)
        raise ProviderError("Falha inesperada ao consultar a Etsy.")

    def _throttle(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = self.config.request_delay - (now - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _retry_delay(attempt: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return min(60.0, max(0.0, float(retry_after)))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    return min(60.0, max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds()))
                except (TypeError, ValueError):
                    pass
        return min(8.0, 0.5 * (2**attempt))
