from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base-agent"

    @abstractmethod
    def handle(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError
