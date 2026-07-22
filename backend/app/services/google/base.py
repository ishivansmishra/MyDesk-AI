from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GoogleTool(ABC):
    name: str = "google_tool"
    description: str = "Base Google Workspace tool"

    @abstractmethod
    def execute(self, service: Any | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError

    def retry(self, fn, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    def log(self, message: str) -> None:
        print(message)
