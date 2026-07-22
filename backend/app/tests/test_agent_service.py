from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.agent_service import AgentService


class FakeCalendarService:
    def __init__(self) -> None:
        self.created_events: list[dict[str, object]] = []
        self._action = None
        self._latest: dict[str, object] | None = None

    def events(self) -> "FakeCalendarService":
        self._action = "events"
        return self

    def list(self, **kwargs: object) -> "FakeCalendarService":
        self._action = "list"
        return self

    def insert(self, calendarId: str, body: dict[str, object], conferenceDataVersion: int = 1) -> "FakeCalendarService":
        self._action = "insert"
        event = {
            "id": "fake-event-id",
            "summary": body.get("summary", ""),
            "start": body.get("start", {}),
            "end": body.get("end", {}),
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self.created_events.append(event)
        self._latest = event
        return self

    def execute(self) -> dict[str, object]:
        if self._action == "list":
            return {"items": []}
        return self._latest or {}


class FakeTaskService:
    def __init__(self) -> None:
        self.task_items: list[dict[str, object]] = []
        self._action = None
        self._latest: dict[str, object] | None = None

    def tasks(self) -> "FakeTaskService":
        self._action = "tasks"
        return self

    def list(self, tasklist: str = "@default", maxResults: int = 50) -> "FakeTaskService":
        self._action = "list"
        return self

    def insert(self, tasklist: str, body: dict[str, object]) -> "FakeTaskService":
        self._action = "insert"
        task = {
            "id": "fake-task-id",
            "title": body.get("title", ""),
            "notes": body.get("notes"),
            "status": "needsAction",
            "due": body.get("due"),
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        self.task_items.append(task)
        self._latest = task
        return self

    def execute(self) -> dict[str, object]:
        if self._action == "list":
            return {"items": self.task_items}
        return self._latest or {}


def test_agent_service_routes_calendar_requests() -> None:
    service = AgentService()
    result = service.handle("Schedule a meeting tomorrow at 3 PM")
    assert result["intent"] == "calendar"
    assert result["reply"] == "What is the meeting title?"


def test_agent_service_routes_task_requests() -> None:
    service = AgentService()
    fake_tasks = FakeTaskService()
    result = service.handle("Create a follow-up task", tasks_service=fake_tasks)
    assert result["intent"] == "tasks"
    assert result["result"]["status"] == "created"
    assert result["result"]["title"] == "Create a follow-up task"


def test_agent_service_plan_day_workflow() -> None:
    service = AgentService()
    fake_calendar = FakeCalendarService()
    fake_tasks = FakeTaskService()
    context = {"user_id": "test-user"}

    result = service.handle(
        "Plan my day",
        context=context,
        calendar_service=fake_calendar,
        tasks_service=fake_tasks,
    )
    assert result["intent"] == "plan_day"
    assert result["result"] is not None
    assert isinstance(result["result"]["suggested_schedule"], list)
    assert result["result"]["suggested_schedule"]

    confirmation = service.handle(
        "Yes",
        context=context,
        calendar_service=fake_calendar,
        tasks_service=fake_tasks,
    )
    assert confirmation["intent"] == "plan_day"
    assert confirmation["result"]["created_events"]
    assert fake_calendar.created_events


def test_agent_service_add_task_follows_up() -> None:
    service = AgentService()
    fake_tasks = FakeTaskService()
    context = {"user_id": "test-user-task"}

    first = service.handle(
        "Add a task",
        context=context,
        calendar_service=None,
        tasks_service=fake_tasks,
    )
    assert first["reply"] == "What should the task be called?"

    second = service.handle(
        "Write weekly report",
        context=context,
        calendar_service=None,
        tasks_service=fake_tasks,
    )
    assert second["intent"] == "tasks"
    assert second["result"]["title"] == "Write weekly report"
    assert fake_tasks.tasks
