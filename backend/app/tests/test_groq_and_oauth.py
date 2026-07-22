{"detail":"Invalid or missing OAuth state"}from app.core.config import settings
from app.services.groq_provider import GroqProvider
from app.services.google import oauth_service as oauth_module
from app.services.google.oauth_service import GoogleOAuthService


def test_groq_provider_fails_gracefully_without_key() -> None:
    provider = GroqProvider()
    response = provider.generate('Hello')
    assert 'not configured' in response.lower() or 'failed' in response.lower()


def test_google_oauth_service_reports_configuration() -> None:
    service = GoogleOAuthService()
    status = service.status()
    assert 'connected' in status
    assert 'configured' in status


def test_google_oauth_service_shares_token_state_between_instances() -> None:
    first_service = GoogleOAuthService()
    first_service._token = {"token": "test-token"}

    second_service = GoogleOAuthService()

    assert second_service._token == {"token": "test-token"}


def test_google_oauth_service_build_auth_url_generates_code_verifier(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")

    service = GoogleOAuthService()
    authorization_url, code_verifier = service.build_auth_url(
        state="test-state",
        redirect_uri="http://localhost/api/v1/oauth/google/callback",
    )

    assert "code_challenge=" in authorization_url
    assert "state=test-state" in authorization_url
    assert isinstance(code_verifier, str)
    assert len(code_verifier) >= 43


def test_google_oauth_service_exchange_code_requires_code_verifier(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")

    service = GoogleOAuthService()

    try:
        service.exchange_code(
            code="dummy-code",
            redirect_uri="http://localhost/api/v1/oauth/google/callback",
            code_verifier=None,
        )
        assert False, "Expected RuntimeError when code verifier is missing"
    except RuntimeError as exc:
        assert "code verifier" in str(exc).lower()
