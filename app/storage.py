from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from app.models import ProcessedFile


class InMemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, ProcessedFile] = {}

    def create(self, **kwargs) -> ProcessedFile:
        item = ProcessedFile(id=str(uuid4()), **kwargs)
        self._items[item.id] = item
        return item

    def get(self, file_id: str) -> ProcessedFile | None:
        return self._items.get(file_id)

    def measurements(self, file_id: str) -> list[dict]:
        item = self._items.get(file_id)
        if item is None:
            return []
        return item.features


store = InMemoryStore()
