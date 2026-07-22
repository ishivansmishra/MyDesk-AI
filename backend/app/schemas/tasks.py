from __future__ import annotations

from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    id: str
    title: str
    notes: str | None = None
    completed: bool = False
    due: str | None = None
    created_at: str


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1)
    notes: str | None = None
    due: str | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    notes: str | None = None
    completed: bool | None = None
    due: str | None = None
