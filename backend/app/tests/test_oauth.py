import urllib.parse

import jwt
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_oauth_flow_endpoint() -> None:
    response = client.get("/api/v1/oauth/google")
    assert response.status_code == 200
    assert "oauth-flow-ready" in response.text


def test_oauth_status_endpoint() -> None:
    response = client.get("/api/v1/oauth/google/status")
    assert response.status_code == 200
    payload = response.json()
    assert "configured" in payload
    assert "connected" in payload


def test_oauth_start_returns_signed_state_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret")

    response = client.get("/api/v1/oauth/google")
    assert response.status_code == 200

    payload = response.json()
    assert "authorization_url" in payload
    assert "state" in payload

    state_token = payload["state"]
    decoded = jwt.decode(state_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert decoded["redirect_target"] == settings.frontend_url
    assert isinstance(decoded["code_verifier"], str)
    assert decoded["code_verifier"]

    auth_url = payload["authorization_url"]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query)
    assert query["state"][0] == state_token
    assert query["redirect_uri"][0] == settings.google_redirect_uri
