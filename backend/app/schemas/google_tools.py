from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateCalendarEventInput(BaseModel):
    summary: str = Field(..., min_length=1)
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)
    timezone: str = Field(..., min_length=1)
    description: str | None = None
    location: str | None = None
    attendees: list[dict[str, str]] | None = None
    conferenceData: dict[str, Any] | None = None


class CreateCalendarEventOutput(BaseModel):
    id: str
    calendar_link: str | None = None
    status: str
    summary: str
    start: str
    end: str
    timezone: str | None = None
    location: str | None = None
    attendees: list[dict[str, Any]] | None = None
    description: str | None = None
    created_at: str | None = None


class CreateTaskInput(BaseModel):
    title: str = Field(..., min_length=1)
    notes: str | None = None
    due: str | None = None


class CreateTaskOutput(BaseModel):
    id: str | None = None
    status: str
    title: str
    notes: str | None = None
    due: str | None = None
    completed: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
