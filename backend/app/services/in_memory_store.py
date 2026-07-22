from __future__ import annotations

from typing import Dict, List
import uuid
from datetime import datetime, timezone


class InMemoryStore:
    def __init__(self) -> None:
        self.events: Dict[str, dict] = {}
        self.tasks: Dict[str, dict] = {}

    def create_event(self, data: dict) -> dict:
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "summary": data["summary"],
            "start": data["start"],
            "end": data["end"],
            "timezone": data.get("timezone"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.events[event_id] = event
        return event

    def list_events(self) -> List[dict]:
        return list(self.events.values())

    def update_event(self, event_id: str, data: dict) -> dict | None:
        event = self.events.get(event_id)
        if not event:
            return None
        event.update(data)
        return event

    def delete_event(self, event_id: str) -> bool:
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False

    def create_task(self, data: dict) -> dict:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": data["title"],
            "notes": data.get("notes"),
            "completed": False,
            "due": data.get("due"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.tasks[task_id] = task
        return task

    def list_tasks(self) -> List[dict]:
        return list(self.tasks.values())

    def update_task(self, task_id: str, data: dict) -> dict | None:
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.update(data)
        return task

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


store = InMemoryStore()
