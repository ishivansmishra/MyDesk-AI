from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.workspace_account import WorkspaceAccount
from app.schemas.tasks import CreateTaskRequest, TaskItem, UpdateTaskRequest
from app.services.auth_service import get_current_user
from app.services.google.oauth_service import GoogleOAuthService

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_tasks_service(current_user: WorkspaceAccount, session: AsyncSession) -> object:
    service = GoogleOAuthService(current_user.id, session)
    try:
        return await service.get_tasks_service()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unable to access Google Tasks.")


@router.get("", response_model=list[TaskItem])
async def list_tasks(
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    service = await _get_tasks_service(current_user, session)
    items = service.tasks().list(tasklist="@default", maxResults=100).execute().get("items", [])
    return [
        {
            "id": item.get("id", ""),
            "title": item.get("title", "Untitled"),
            "notes": item.get("notes"),
            "completed": item.get("status") == "completed",
            "due": item.get("due"),
            "created_at": item.get("updated", ""),
        }
        for item in items
    ]


@router.post("", response_model=TaskItem)
async def create_task(
    payload: CreateTaskRequest,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_tasks_service(current_user, session)
    created = service.tasks().insert(tasklist="@default", body={"title": payload.title, "notes": payload.notes, "due": payload.due}).execute()
    return {
        "id": created.get("id", ""),
        "title": created.get("title", payload.title),
        "notes": created.get("notes"),
        "completed": created.get("status") == "completed",
        "due": created.get("due"),
        "created_at": created.get("updated", ""),
    }


@router.put("/{task_id}", response_model=TaskItem)
async def update_task(
    task_id: str,
    payload: UpdateTaskRequest,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_tasks_service(current_user, session)
    body: dict[str, object] = {}
    if payload.title is not None:
        body["title"] = payload.title
    if payload.notes is not None:
        body["notes"] = payload.notes
    if payload.completed is not None:
        body["status"] = "completed" if payload.completed else "needsAction"
    if payload.due is not None:
        body["due"] = payload.due
    updated = service.tasks().patch(tasklist="@default", task=task_id, body=body).execute()
    return {
        "id": updated.get("id", task_id),
        "title": updated.get("title", ""),
        "notes": updated.get("notes"),
        "completed": updated.get("status") == "completed",
        "due": updated.get("due"),
        "created_at": updated.get("updated", ""),
    }


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: WorkspaceAccount = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = await _get_tasks_service(current_user, session)
    service.tasks().delete(tasklist="@default", task=task_id).execute()
    return {"status": "deleted"}
