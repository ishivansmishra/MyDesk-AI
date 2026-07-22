from __future__ import annotations

from pydantic import BaseModel, Field


class AgentIntentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str | None = None


class AgentIntentResponse(BaseModel):
    reply: str
    intent: str
    status: str
