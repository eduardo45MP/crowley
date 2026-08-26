from __future__ import annotations

from typing import Any


class ScreenshotCollector:
    def collect(self, products: list[Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for product in products:
            for index, image_url in enumerate(product.image_urls or [], start=1):
                results.append({
                    "product_id": getattr(product, "id", None),
                    "source_url": product.url,
                    "image_url": image_url,
                    "local_path": None,
                    "captured_at": getattr(product, "collected_at", None).isoformat() if getattr(product, "collected_at", None) is not None else None,
                    "image_type": "reference",
                })
        return results[:20]
