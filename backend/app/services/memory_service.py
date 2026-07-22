from __future__ import annotations

from typing import Any


class MemoryService:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def remember(self, user_id: str, key: str, value: Any) -> None:
        self._store.setdefault(user_id, {})[key] = value

    def recall(self, user_id: str, key: str, default: Any | None = None) -> Any:
        return self._store.get(user_id, {}).get(key, default)
