from __future__ import annotations

from typing import Any

from app.services.groq_provider import GroqProvider


class LLMProvider:
    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider or "groq"
        self.groq = GroqProvider()

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if self.provider == "groq":
            return self.groq.generate(prompt, **kwargs)
        return f"{self.provider} provider is not configured."
