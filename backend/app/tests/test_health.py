from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Schedule a meeting tomorrow", "user_id": "user-1"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "calendar"
