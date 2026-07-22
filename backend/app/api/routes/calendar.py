from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.workspace_account import WorkspaceAccount
from app.schemas.calendar import CalendarEvent, CreateCalendarEventRequest, UpdateCalendarEventRequest
from app.services.auth_service import get_current_user
from app.services.google.oauth_service import GoogleOAuthService

router = APIRouter(prefix="/calendar", tags=["calendar"])


async def _get_calendar_service(current_user: WorkspaceAccount, session: AsyncSession) -> object:
    service = GoogleOAuthService(current_user.id, session)
    try:
        return await service.get_calendar_service()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unable to access Google Calendar.") from exc


@router.get("", response_model=list[CalendarEvent])
async def list_events(
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    service = await _get_calendar_service(current_user, session)
    items = service.events().list(calendarId="primary", maxResults=20).execute().get("items", [])
    return [
        {
            "id": item.get("id", ""),
            "summary": item.get("summary", "Untitled"),
            "start": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date", ""),
            "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date", ""),
            "timezone": item.get("start", {}).get("timeZone"),
            "created_at": item.get("created", ""),
        }
        for item in items
    ]


@router.post("", response_model=CalendarEvent)
async def create_event(
    payload: CreateCalendarEventRequest,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_calendar_service(current_user, session)
    google_payload = {
        "summary": payload.summary,
        "start": {"dateTime": payload.start},
        "end": {"dateTime": payload.end},
    }
    if payload.timezone:
        google_payload["start"]["timeZone"] = payload.timezone
        google_payload["end"]["timeZone"] = payload.timezone
    created = service.events().insert(calendarId="primary", body=google_payload).execute()
    return {
        "id": created.get("id", ""),
        "summary": created.get("summary", payload.summary),
        "start": created.get("start", {}).get("dateTime") or created.get("start", {}).get("date", payload.start),
        "end": created.get("end", {}).get("dateTime") or created.get("end", {}).get("date", payload.end),
        "timezone": created.get("start", {}).get("timeZone") or payload.timezone,
        "created_at": created.get("created", ""),
    }


@router.put("/{event_id}", response_model=CalendarEvent)
async def update_event(
    event_id: str,
    payload: UpdateCalendarEventRequest,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_calendar_service(current_user, session)
    google_payload: dict[str, object] = {}
    if payload.summary is not None:
        google_payload["summary"] = payload.summary
    if payload.start is not None:
        google_payload["start"] = {"dateTime": payload.start}
    if payload.end is not None:
        google_payload["end"] = {"dateTime": payload.end}
    if payload.timezone is not None:
        if "start" in google_payload:
            google_payload["start"] = {"dateTime": payload.start, "timeZone": payload.timezone}
        if "end" in google_payload:
            google_payload["end"] = {"dateTime": payload.end, "timeZone": payload.timezone}
    updated = service.events().patch(calendarId="primary", eventId=event_id, body=google_payload).execute()
    return {
        "id": updated.get("id", event_id),
        "summary": updated.get("summary", ""),
        "start": updated.get("start", {}).get("dateTime") or updated.get("start", {}).get("date", ""),
        "end": updated.get("end", {}).get("dateTime") or updated.get("end", {}).get("date", ""),
        "timezone": updated.get("start", {}).get("timeZone"),
        "created_at": updated.get("created", ""),
    }


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_calendar_service(current_user, session)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return {"status": "deleted"}
