from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.schemas.google_tools import CreateCalendarEventInput, CreateCalendarEventOutput
from app.services.google.base import GoogleTool

logger = logging.getLogger(__name__)


class CalendarTool(GoogleTool):
    name = "calendar"
    description = "Create, read, update, and delete Google Calendar events"

    def execute(self, service: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        return self.create_event(service=service, **kwargs)

    def create_event(
        self,
        service: Any,
        summary: str,
        start: str,
        end: str,
        timezone: str,
        description: str | None = None,
        attendees: list[dict[str, str]] | None = None,
        location: str | None = None,
        conference_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = CreateCalendarEventInput(
            summary=summary,
            start=start,
            end=end,
            timezone=timezone,
        )
        self.log(f"Calendar tool create_event called with payload: {payload.model_dump()}")

        body: dict[str, Any] = {
            "summary": payload.summary,
            "description": description or "",
            "start": {"dateTime": payload.start, "timeZone": payload.timezone},
            "end": {"dateTime": payload.end, "timeZone": payload.timezone},
        }
        if attendees:
            body["attendees"] = attendees
        if location:
            body["location"] = location
        if conference_data:
            body["conferenceData"] = conference_data

        logger.info("Google Calendar request calendarId=%s body=%s", "primary", body)
        created = service.events().insert(calendarId="primary", body=body, conferenceDataVersion=1).execute()
        logger.info("Google Calendar response=%s", created)

        if not created or not created.get("id"):
            raise RuntimeError("Google Calendar API did not return a created event ID")

        event_start = created.get("start", {})
        event_end = created.get("end", {})
        timezone_value = event_start.get("timeZone") or payload.timezone
        return {
            "id": created.get("id", ""),
            "calendar_link": created.get("htmlLink", ""),
            "status": created.get("status", "confirmed"),
            "summary": created.get("summary", payload.summary),
            "start": event_start.get("dateTime") or event_start.get("date", payload.start),
            "end": event_end.get("dateTime") or event_end.get("date", payload.end),
            "timezone": timezone_value,
            "location": created.get("location"),
            "attendees": created.get("attendees"),
            "description": created.get("description"),
            "created_at": created.get("created", ""),
        }

    def list_events(
        self,
        service: Any,
        time_min: str | None = None,
        time_max: str | None = None,
        query: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "calendarId": "primary",
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": max_results,
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if query:
            params["q"] = query

        logger.info("Google Calendar list_events request params=%s", params)
        response = service.events().list(**params).execute()
        logger.info("Google Calendar list_events response=%s", response)
        return response.get("items", [])

    def update_event(self, service: Any, event_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        if not updates:
            raise ValueError("No update fields provided for calendar event")

        logger.info("Google Calendar update_event eventId=%s updates=%s", event_id, updates)
        updated = service.events().patch(calendarId="primary", eventId=event_id, body=updates).execute()
        logger.info("Google Calendar update_event response=%s", updated)
        if not updated or not updated.get("id"):
            raise RuntimeError("Google Calendar API failed to update the event")
        return updated

    def delete_event(self, service: Any, event_id: str) -> None:
        logger.info("Google Calendar delete_event eventId=%s", event_id)
        response = service.events().delete(calendarId="primary", eventId=event_id).execute()
        logger.info("Google Calendar delete_event response=%s", response)

    def search_events(
        self,
        service: Any,
        query: str | None = None,
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "calendarId": "primary",
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": max_results,
        }
        if query:
            params["q"] = query
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max

        logger.info("Google Calendar search_events request params=%s", params)
        response = service.events().list(**params).execute()
        logger.info("Google Calendar search_events response=%s", response)
        return response.get("items", [])
