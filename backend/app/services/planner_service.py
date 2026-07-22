from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class PlannerService:
    def build_suggested_schedule(
        self,
        now: datetime,
        events: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        local_now = now.astimezone()
        today = local_now.date()
        timezone_name = local_now.tzname() or "UTC"

        if events:
            return []

        blocks = [
            ("Morning planning", 9, 0, 9, 30),
            ("Deep work", 10, 0, 12, 0),
            ("Lunch", 12, 30, 13, 30),
            ("Meetings", 14, 0, 16, 0),
            ("Exercise", 16, 0, 17, 0),
            ("Personal time", 18, 0, 19, 0),
            ("Review tomorrow", 20, 0, 20, 30),
        ]

        if tasks:
            blocks.insert(4, ("Review tasks", 17, 0, 17, 30))

        schedule: list[dict[str, Any]] = []
        for summary, sh, sm, eh, em in blocks:
            start = datetime(
                year=today.year,
                month=today.month,
                day=today.day,
                hour=sh,
                minute=sm,
                tzinfo=local_now.tzinfo,
            )
            end = datetime(
                year=today.year,
                month=today.month,
                day=today.day,
                hour=eh,
                minute=em,
                tzinfo=local_now.tzinfo,
            )
            schedule.append(
                {
                    "summary": summary,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "timezone": timezone_name,
                }
            )
        return schedule

    def format_schedule_summary(self, events: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for item in events:
            start = item["start"]
            end = item["end"]
            summary = item["summary"]
            lines.append(f"- {summary}: {start} to {end}")
        return "\n".join(lines)

    def summarize_existing_day(self, events: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> str:
        event_count = len(events)
        task_count = len(tasks)
        if event_count == 0:
            return "I do not see any events scheduled today."
        earliest = events[0].get("start", {}).get("dateTime") or events[0].get("start", {}).get("date")
        return f"I found {event_count} event(s) and {task_count} task(s) for today. Your first scheduled item starts at {earliest}."
