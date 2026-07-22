from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    result: dict[str, object] | None = None
