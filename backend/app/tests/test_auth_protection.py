from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_calendar_requires_auth_without_token() -> None:
    response = client.get("/api/v1/calendar")
    assert response.status_code == 401


def test_tasks_requires_auth_without_token() -> None:
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401
