from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.config import settings


class GroqProvider:
    def __init__(self) -> None:
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not self.api_key:
            return "Groq is not configured. Provide GROQ_API_KEY in backend/.env."

        if os.getenv("PYTEST_CURRENT_TEST") or settings.environment.lower() == "test":
            return "Groq request failed: test environment does not call the live API."

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = httpx.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover - defensive path
            return f"Groq request failed: {exc}"
