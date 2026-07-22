from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import calendar as calendar_routes
from app.api.routes import tasks as tasks_routes
from app.main import app
from app.repositories.workspace_account_repository import WorkspaceAccountRepository
from app.services.auth_service import AuthService

client = TestClient(app)


def _create_auth_token() -> str:
    return AuthService().create_access_token('fake-user-id')


async def _fake_get_by_id(self, account_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id='fake-user-id',
        google_user_id='fake-google-user-id',
        user_email='test-user@example.com',
        name='Test User',
        provider='google',
        connected_at=datetime.now(timezone.utc),
        status='connected',
        profile_picture=None,
        access_token='token',
        refresh_token='refresh-token',
        token_expiry=datetime.now(timezone.utc),
    )


class FakeCalendarService:
    def __init__(self) -> None:
        self.events_list: list[dict] = []
        self._latest: dict[str, object] | None = None
        self._last_action: str | None = None

    def events(self) -> 'FakeCalendarService':
        self._last_action = 'events'
        return self

    def list(self, **kwargs: object) -> 'FakeCalendarService':
        self._last_action = 'list'
        return self

    def execute(self) -> dict:
        if self._last_action == 'list':
            return {'items': self.events_list}
        return self._latest or {}

    def insert(self, calendarId: str, body: dict[str, object]) -> 'FakeCalendarService':
        self._last_action = 'insert'
        event = {
            'id': str(uuid4()),
            'summary': body.get('summary', ''),
            'start': {'dateTime': body.get('start', {}).get('dateTime')},
            'end': {'dateTime': body.get('end', {}).get('dateTime')},
            'created': datetime.now(timezone.utc).isoformat(),
        }
        self.events_list.append(event)
        self._latest = event
        return self

    def patch(self, calendarId: str, eventId: str, body: dict[str, object]) -> 'FakeCalendarService':
        self._last_action = 'patch'
        for event in self.events_list:
            if event['id'] == eventId:
                if 'summary' in body:
                    event['summary'] = body['summary']
                if 'start' in body:
                    event['start'] = body['start']
                if 'end' in body:
                    event['end'] = body['end']
                self._latest = event
                return self
        raise ValueError('Event not found')

    def delete(self, calendarId: str, eventId: str) -> 'FakeCalendarService':
        self._last_action = 'delete'
        self.events_list = [event for event in self.events_list if event['id'] != eventId]
        self._latest = None
        return self


class FakeTasksService:
    def __init__(self) -> None:
        self.tasks_list: list[dict] = []
        self._latest: dict[str, object] | None = None
        self._last_action: str | None = None

    def tasks(self) -> 'FakeTasksService':
        self._last_action = 'tasks'
        return self

    def tasklists(self) -> 'FakeTasksService':
        self._last_action = 'tasklists'
        return self

    def list(self, **kwargs: object) -> 'FakeTasksService':
        self._last_action = 'list'
        return self

    def execute(self) -> dict:
        if self._last_action == 'list':
            return {'items': self.tasks_list}
        return self._latest or {}

    def insert(self, tasklist: str, body: dict[str, object]) -> 'FakeTasksService':
        self._last_action = 'insert'
        task = {
            'id': str(uuid4()),
            'title': body.get('title', ''),
            'notes': body.get('notes'),
            'status': 'needsAction',
            'due': body.get('due'),
            'updated': datetime.now(timezone.utc).isoformat(),
        }
        self.tasks_list.append(task)
        self._latest = task
        return self

    def patch(self, tasklist: str, task: str, body: dict[str, object]) -> 'FakeTasksService':
        for item in self.tasks_list:
            if item['id'] == task:
                if 'title' in body:
                    item['title'] = body['title']
                if 'notes' in body:
                    item['notes'] = body['notes']
                if 'status' in body:
                    item['status'] = body['status']
                if 'due' in body:
                    item['due'] = body['due']
                item['updated'] = datetime.now(timezone.utc).isoformat()
                self._latest = item
                return self
        raise ValueError('Task not found')

    def delete(self, tasklist: str, task: str) -> 'FakeTasksService':
        self.tasks_list = [item for item in self.tasks_list if item['id'] != task]
        return self


def test_calendar_crud_flow(monkeypatch) -> None:
    token = _create_auth_token()
    fake_calendar = FakeCalendarService()
    async def _fake_get_calendar_service(current_user, session):
        return fake_calendar

    monkeypatch.setattr(
        WorkspaceAccountRepository,
        'get_by_id',
        _fake_get_by_id,
        raising=True,
    )
    monkeypatch.setattr(calendar_routes, '_get_calendar_service', _fake_get_calendar_service)

    response = client.post(
        '/api/v1/calendar',
        json={'summary': 'Planning sync', 'start': '2026-07-22T09:00:00', 'end': '2026-07-22T10:00:00'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    event_id = response.json()['id']

    list_response = client.get('/api/v1/calendar', headers={'Authorization': f'Bearer {token}'})
    assert list_response.status_code == 200
    assert any(item['id'] == event_id for item in list_response.json())

    update_response = client.put(
        f'/api/v1/calendar/{event_id}',
        json={'summary': 'Updated sync'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert update_response.status_code == 200
    assert update_response.json()['summary'] == 'Updated sync'

    delete_response = client.delete(f'/api/v1/calendar/{event_id}', headers={'Authorization': f'Bearer {token}'})
    assert delete_response.status_code == 200


def test_tasks_crud_flow(monkeypatch) -> None:
    token = _create_auth_token()
    fake_tasks = FakeTasksService()
    async def _fake_get_tasks_service(current_user, session):
        return fake_tasks

    monkeypatch.setattr(
        WorkspaceAccountRepository,
        'get_by_id',
        _fake_get_by_id,
        raising=True,
    )
    monkeypatch.setattr(tasks_routes, '_get_tasks_service', _fake_get_tasks_service)

    response = client.post(
        '/api/v1/tasks',
        json={'title': 'Submit report', 'notes': 'Due tomorrow'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    task_id = response.json()['id']

    list_response = client.get('/api/v1/tasks', headers={'Authorization': f'Bearer {token}'})
    assert list_response.status_code == 200
    assert any(item['id'] == task_id for item in list_response.json())

    update_response = client.put(
        f'/api/v1/tasks/{task_id}',
        json={'completed': True},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert update_response.status_code == 200
    assert update_response.json()['completed'] is True

    delete_response = client.delete(f'/api/v1/tasks/{task_id}', headers={'Authorization': f'Bearer {token}'})
    assert delete_response.status_code == 200
