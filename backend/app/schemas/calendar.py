from __future__ import annotations

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: str
    end: str
    timezone: str | None = None
    created_at: str


class CreateCalendarEventRequest(BaseModel):
    summary: str = Field(..., min_length=1)
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)
    timezone: str | None = None


class UpdateCalendarEventRequest(BaseModel):
    summary: str | None = None
    start: str | None = None
    end: str | None = None
    timezone: str | None = None
