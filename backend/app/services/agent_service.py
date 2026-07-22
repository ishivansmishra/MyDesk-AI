from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.google.calendar_tool import CalendarTool
from app.services.google.tasks_tool import TasksTool
from app.services.llm_provider import LLMProvider
from app.services.memory_service import MemoryService
from app.services.planner_service import PlannerService


class AgentService:
    def __init__(self) -> None:
        self.calendar_tool = CalendarTool()
        self.tasks_tool = TasksTool()
        self.llm_provider = LLMProvider()
        self.memory = MemoryService()
        self.planner = PlannerService()

    def get_intent(self, message: str) -> str:
        lowered = message.lower().strip()
        if any(phrase in lowered for phrase in ["plan my day", "plan the day", "daily plan", "plan today", "plan my schedule", "plan schedule"]):
            return "plan_day"
        if any(phrase in lowered for phrase in ["schedule a meeting", "schedule meeting", "book meeting", "book an appointment", "set up a meeting"]):
            return "schedule_meeting"
        if any(phrase in lowered for phrase in ["add a task", "create a task", "new task", "add task", "create task"]):
            return "add_task"
        if re.search(r"\b(list|show)\s+(my\s+)?tasks\b", lowered):
            return "list_tasks"
        if re.search(r"\b(list|show)\s+(my\s+)?(calendar|events)\b", lowered):
            return "list_calendar"
        if any(keyword in lowered for keyword in ["task", "todo", "to-do"]):
            return "tasks"
        if any(keyword in lowered for keyword in ["calendar", "event", "meeting", "appointment", "schedule"]):
            return "calendar"
        return "assistant"

    def required_services(self, user_id: str, message: str) -> dict[str, bool]:
        pending = self.memory.recall(user_id, "pending", {})
        if pending:
            if pending.get("type") == "plan_day_confirmation":
                return {"calendar": True, "tasks": False}
            if pending.get("type") == "task_creation":
                return {"calendar": False, "tasks": True}
            if pending.get("type") == "meeting_creation":
                return {"calendar": True, "tasks": False}
        intent = self.get_intent(message)
        if intent == "plan_day":
            return {"calendar": True, "tasks": True}
        if intent in ["schedule_meeting", "list_calendar", "calendar"]:
            return {"calendar": True, "tasks": False}
        if intent in ["add_task", "list_tasks", "tasks"]:
            return {"calendar": False, "tasks": True}
        return {"calendar": False, "tasks": False}

    def handle(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        calendar_service: Any | None = None,
        tasks_service: Any | None = None,
    ) -> dict[str, Any]:
        user_id = (context or {}).get("user_id", "default")
        message = message.strip()
        pending = self.memory.recall(user_id, "pending", {})

        if pending:
            return self._handle_pending(user_id, message, pending, calendar_service, tasks_service)

        intent = self.get_intent(message)
        self.memory.remember(user_id, "last_intent", intent)
        self.memory.remember(user_id, "last_message", message)

        if intent == "plan_day":
            return self._handle_plan_day(user_id, calendar_service, tasks_service)

        if intent == "add_task":
            return self._begin_task_creation(user_id)

        if intent == "schedule_meeting":
            return self._begin_meeting_creation(user_id)

        if intent == "list_tasks":
            return self._list_tasks(user_id, tasks_service)

        if intent == "list_calendar":
            return self._list_calendar(user_id, calendar_service)

        if intent == "tasks":
            return self._create_task_from_message(user_id, message, tasks_service)

        if intent == "calendar":
            return self._create_calendar_event_from_message(user_id, message, calendar_service)

        return {
            "reply": "I can help with your calendar and tasks. What would you like to do?",
            "intent": "assistant",
            "result": None,
        }

    def _handle_pending(
        self,
        user_id: str,
        message: str,
        pending: dict[str, Any],
        calendar_service: Any | None,
        tasks_service: Any | None,
    ) -> dict[str, Any]:
        if pending.get("type") == "plan_day_confirmation":
            answer = self._normalize_yes_no(message)
            if answer == "yes":
                schedule = pending.get("schedule", [])
                if calendar_service is None:
                    raise RuntimeError("Google Calendar service is unavailable for plan day workflow")
                created_events = []
                for item in schedule:
                    created = self.calendar_tool.create_event(
                        service=calendar_service,
                        summary=item["summary"],
                        start=item["start"],
                        end=item["end"],
                        timezone=item["timezone"],
                    )
                    created_events.append(created)
                self.memory.remember(user_id, "pending", {})
                return {
                    "reply": f"I added the suggested schedule to your calendar with {len(created_events)} events.",
                    "intent": "plan_day",
                    "result": {"created_events": created_events},
                }
            if answer == "no":
                self.memory.remember(user_id, "pending", {})
                return {
                    "reply": "Okay, I won't add the suggested schedule to your calendar.",
                    "intent": "plan_day",
                    "result": {"created_events": []},
                }
            return {
                "reply": "Would you like me to add the suggested schedule to your Google Calendar? Please answer yes or no.",
                "intent": "plan_day",
                "result": None,
            }

        if pending.get("type") == "task_creation":
            if tasks_service is None:
                raise RuntimeError("Google Tasks service is unavailable for task creation")
            title = message.strip()
            if not title:
                return {
                    "reply": "What should the task be called?",
                    "intent": "tasks",
                    "result": None,
                }
            created = self.tasks_tool.execute(service=tasks_service, action="create", title=title)
            self.memory.remember(user_id, "pending", {})
            return {
                "reply": f"Created task '{created.get('title', title)}'.",
                "intent": "tasks",
                "result": created,
            }

        if pending.get("type") == "meeting_creation":
            if calendar_service is None:
                raise RuntimeError("Google Calendar service is unavailable for meeting creation")
            fields = pending.get("fields", {"title": None, "start": None, "duration": None})
            if not fields.get("title"):
                fields["title"] = message
                self.memory.remember(user_id, "pending", {"type": "meeting_creation", "fields": fields})
                return {
                    "reply": "When should I schedule it?",
                    "intent": "calendar",
                    "result": None,
                }
            if not fields.get("start"):
                start = self._parse_date_time(message)
                if start is None:
                    return {
                        "reply": "I couldn't understand the meeting time. When should I schedule it?",
                        "intent": "calendar",
                        "result": None,
                    }
                fields["start"] = start
                self.memory.remember(user_id, "pending", {"type": "meeting_creation", "fields": fields})
                return {
                    "reply": "How long should it last?",
                    "intent": "calendar",
                    "result": None,
                }
            if not fields.get("duration"):
                duration = self._parse_duration(message)
                if duration is None:
                    return {
                        "reply": "How long should the meeting last?",
                        "intent": "calendar",
                        "result": None,
                    }
                fields["duration"] = duration
            start = fields["start"]
            end = start + fields["duration"]
            timezone_name = start.tzname() or "UTC"
            created = self.calendar_tool.create_event(
                service=calendar_service,
                summary=fields["title"],
                start=start.isoformat(),
                end=end.isoformat(),
                timezone=timezone_name,
            )
            self.memory.remember(user_id, "pending", {})
            return {
                "reply": f"Scheduled '{created.get('summary', fields['title'])}' on your calendar.",
                "intent": "calendar",
                "result": created,
            }

        return {
            "reply": "I didn't understand that request. Can you tell me what you'd like to do?",
            "intent": "assistant",
            "result": None,
        }

    def _handle_plan_day(self, user_id: str, calendar_service: Any | None, tasks_service: Any | None) -> dict[str, Any]:
        if calendar_service is None or tasks_service is None:
            raise RuntimeError("Google Calendar and Google Tasks services are required for planning your day")
        now = datetime.now(timezone.utc)
        window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(days=1)
        events = self.calendar_tool.list_events(
            calendar_service,
            time_min=window_start.isoformat().replace("+00:00", "Z"),
            time_max=window_end.isoformat().replace("+00:00", "Z"),
            max_results=50,
        )
        tasks = self.tasks_tool.list_tasks(tasks_service, max_results=50)
        if events:
            return {
                "reply": self.planner.summarize_existing_day(events, tasks),
                "intent": "plan_day",
                "result": {"events": events, "tasks": tasks},
            }
        suggested = self.planner.build_suggested_schedule(now, events, tasks)
        self.memory.remember(user_id, "pending", {"type": "plan_day_confirmation", "schedule": suggested})
        return {
            "reply": "I found no events for today and generated a suggested schedule. Would you like me to add it to your Google Calendar?",
            "intent": "plan_day",
            "result": {"suggested_schedule": suggested, "tasks": tasks},
        }

    def _begin_task_creation(self, user_id: str) -> dict[str, Any]:
        self.memory.remember(user_id, "pending", {"type": "task_creation"})
        return {
            "reply": "What should the task be called?",
            "intent": "tasks",
            "result": None,
        }

    def _begin_meeting_creation(self, user_id: str) -> dict[str, Any]:
        self.memory.remember(user_id, "pending", {"type": "meeting_creation", "fields": {"title": None, "start": None, "duration": None}})
        return {
            "reply": "What is the meeting title?",
            "intent": "calendar",
            "result": None,
        }

    def _list_tasks(self, user_id: str, tasks_service: Any | None) -> dict[str, Any]:
        if tasks_service is None:
            raise RuntimeError("Google Tasks service is unavailable for listing tasks")
        items = self.tasks_tool.list_tasks(tasks_service, max_results=50)
        return {
            "reply": f"I found {len(items)} task(s).",
            "intent": "list_tasks",
            "result": {"tasks": items},
        }

    def _list_calendar(self, user_id: str, calendar_service: Any | None) -> dict[str, Any]:
        if calendar_service is None:
            raise RuntimeError("Google Calendar service is unavailable for listing events")
        now = datetime.now(timezone.utc)
        window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(days=1)
        items = self.calendar_tool.list_events(
            calendar_service,
            time_min=window_start.isoformat().replace("+00:00", "Z"),
            time_max=window_end.isoformat().replace("+00:00", "Z"),
            max_results=50,
        )
        return {
            "reply": f"I found {len(items)} event(s) for today.",
            "intent": "list_calendar",
            "result": {"events": items},
        }

    def _create_task_from_message(self, user_id: str, message: str, tasks_service: Any | None) -> dict[str, Any]:
        if tasks_service is None:
            raise RuntimeError("Google Tasks service is unavailable for task creation")
        title = self._extract_task_title(message)
        if not title or len(title) < 3:
            return self._begin_task_creation(user_id)
        created = self.tasks_tool.execute(service=tasks_service, action="create", title=title)
        return {
            "reply": f"Created task '{created.get('title', title)}'.",
            "intent": "tasks",
            "result": created,
        }

    def _create_calendar_event_from_message(self, user_id: str, message: str, calendar_service: Any | None) -> dict[str, Any]:
        if calendar_service is None:
            raise RuntimeError("Google Calendar service is unavailable for calendar event creation")
        payload = self._build_calendar_payload(message)
        created = self.calendar_tool.execute(service=calendar_service, **payload)
        return {
            "reply": f"Created '{created.get('summary', payload['summary'])}' on your calendar.",
            "intent": "calendar",
            "result": created,
        }

    def _build_calendar_payload(self, message: str) -> dict[str, str | None]:
        lowered = message.lower()
        local_now = datetime.now(timezone.utc).astimezone()
        date = local_now
        if "tomorrow" in lowered:
            date += timedelta(days=1)
        elif "today" in lowered:
            date = date
        else:
            date += timedelta(days=1)

        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lowered)
        hour = 10
        minute = 0
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

        start = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        summary = "Meeting" if "meeting" in lowered or "appointment" in lowered else message.strip()
        if not summary:
            summary = "Meeting"

        timezone_name = local_now.tzname() or "UTC"
        return {
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": timezone_name,
        }

    def _build_task_payload(self, message: str) -> dict[str, str | None]:
        title = self._extract_task_title(message) or message.strip()
        if not title:
            title = "Follow up"
        due_date = None
        lowered = message.lower()
        local_now = datetime.now(timezone.utc).astimezone()
        if "tomorrow" in lowered:
            due_date = (local_now + timedelta(days=1)).date().isoformat()
        elif "today" in lowered:
            due_date = local_now.date().isoformat()
        return {
            "title": title,
            "notes": message.strip(),
            "due": due_date,
        }

    def _extract_task_title(self, message: str) -> str | None:
        lowered = message.lower().strip()
        for prefix in ["add a task to", "add a task", "create a task", "add task", "create task"]:
            if lowered.startswith(prefix):
                stripped = message[len(prefix) :].strip()
                return stripped or None
        return message.strip()

    def _parse_date_time(self, message: str) -> datetime | None:
        now = datetime.now(timezone.utc).astimezone()
        lowered = message.lower()
        offset = 0
        if "tomorrow" in lowered:
            offset = 1
        elif "today" in lowered:
            offset = 0

        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
        if not time_match:
            return None
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        candidate = now + timedelta(days=offset)
        return candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _parse_duration(self, message: str) -> timedelta | None:
        lowered = message.lower()
        hour_match = re.search(r"(\d+)\s*(?:hours|hour|hrs|hr|h)\b", lowered)
        minute_match = re.search(r"(\d+)\s*(?:minutes|minute|mins|min)\b", lowered)
        if hour_match:
            return timedelta(hours=int(hour_match.group(1)))
        if minute_match:
            return timedelta(minutes=int(minute_match.group(1)))
        if "half hour" in lowered or "30 minutes" in lowered:
            return timedelta(minutes=30)
        return None

    def _normalize_yes_no(self, message: str) -> str | None:
        normalized = message.strip().lower()
        if normalized in {"yes", "y", "sure", "please do", "go ahead", "yeah", "yep", "please"}:
            return "yes"
        if normalized in {"no", "n", "nope", "not now", "don't", "do not"}:
            return "no"
        return None
