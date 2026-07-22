from __future__ import annotations

import logging
from typing import Any

from app.schemas.google_tools import CreateTaskInput, CreateTaskOutput
from app.services.google.base import GoogleTool

logger = logging.getLogger(__name__)


class TasksTool(GoogleTool):
    name = "tasks"
    description = "Create, read, update, complete, and list Google Tasks"

    def execute(self, service: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        if service is None:
            payload = CreateTaskInput(**kwargs)
            output = CreateTaskOutput(status="created", title=payload.title, notes=payload.notes, due=payload.due)
            self.log(f"Tasks tool executed for {payload.title}")
            return output.model_dump()

        action = kwargs.pop("action", "create")
        if action == "create":
            return self.create_task(service, **kwargs)
        if action == "update":
            return self.update_task(service, **kwargs)
        if action == "delete":
            return self.delete_task(service, **kwargs)
        if action == "complete":
            return self.complete_task(service, **kwargs)
        if action == "list":
            return {"items": self.list_tasks(service, **kwargs)}
        raise ValueError(f"Unknown tasks action: {action}")

    def create_task(self, service: Any, title: str, notes: str | None = None, due: str | None = None) -> dict[str, Any]:
        payload = CreateTaskInput(title=title, notes=notes, due=due)
        body: dict[str, Any] = {"title": payload.title}
        if payload.notes:
            body["notes"] = payload.notes
        if payload.due:
            body["due"] = payload.due

        logger.info("Google Tasks create_task request body=%s", body)
        created = service.tasks().insert(tasklist="@default", body=body).execute()
        logger.info("Google Tasks create_task response=%s", created)
        if not created or not created.get("id"):
            raise RuntimeError("Google Tasks API did not return a created task ID")
        return {
            "id": created.get("id", ""),
            "status": "created",
            "title": created.get("title", payload.title),
            "notes": created.get("notes"),
            "completed": created.get("status") == "completed",
            "due": created.get("due"),
            "updated_at": created.get("updated", ""),
        }

    def update_task(self, service: Any, task_id: str, title: str | None = None, notes: str | None = None, completed: bool | None = None, due: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if notes is not None:
            body["notes"] = notes
        if completed is not None:
            body["status"] = "completed" if completed else "needsAction"
        if due is not None:
            body["due"] = due

        if not body:
            raise ValueError("No update fields provided for task")

        logger.info("Google Tasks update_task taskId=%s body=%s", task_id, body)
        updated = service.tasks().patch(tasklist="@default", task=task_id, body=body).execute()
        logger.info("Google Tasks update_task response=%s", updated)
        if not updated or not updated.get("id"):
            raise RuntimeError("Google Tasks API did not return an updated task ID")
        return {
            "id": updated.get("id", ""),
            "title": updated.get("title", title or updated.get("title", "")),
            "notes": updated.get("notes"),
            "completed": updated.get("status") == "completed",
            "due": updated.get("due"),
            "updated_at": updated.get("updated", ""),
        }

    def delete_task(self, service: Any, task_id: str) -> dict[str, Any]:
        logger.info("Google Tasks delete_task taskId=%s", task_id)
        service.tasks().delete(tasklist="@default", task=task_id).execute()
        return {"status": "deleted", "id": task_id}

    def complete_task(self, service: Any, task_id: str) -> dict[str, Any]:
        logger.info("Google Tasks complete_task taskId=%s", task_id)
        updated = service.tasks().patch(tasklist="@default", task=task_id, body={"status": "completed"}).execute()
        logger.info("Google Tasks complete_task response=%s", updated)
        if not updated or not updated.get("id"):
            raise RuntimeError("Google Tasks API did not return an updated task ID")
        return {
            "id": updated.get("id", ""),
            "status": "completed",
            "title": updated.get("title", ""),
            "notes": updated.get("notes"),
            "due": updated.get("due"),
            "updated_at": updated.get("updated", ""),
        }

    def list_tasks(self, service: Any, max_results: int = 50) -> list[dict[str, Any]]:
        logger.info("Google Tasks list_tasks request maxResults=%s", max_results)
        response = service.tasks().list(tasklist="@default", maxResults=max_results).execute()
        logger.info("Google Tasks list_tasks response=%s", response)
        return response.get("items", [])
