from __future__ import annotations

import json
import re
from pathlib import Path

from crawler.models import SearchResult
from crawler.storage.base import ResultStore


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "search"


class JsonResultStore(ResultStore):
    def __init__(self, output: str | Path | None = None) -> None:
        self.output = Path(output) if output else Path("data/raw")

    def save(self, result: SearchResult) -> Path:
        if self.output.suffix.lower() == ".json":
            path = self.output
        else:
            timestamp = result.collected_at.strftime("%Y-%m-%dT%H-%M-%S")
            path = self.output / result.marketplace.value / _slugify(result.query) / f"{timestamp}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path
