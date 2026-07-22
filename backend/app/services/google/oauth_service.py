from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import logging

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.workspace_account import WorkspaceAccount
from app.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)

USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks",
]


class GoogleOAuthService:
    def __init__(self, user_id: str | None = None, session: AsyncSession | None = None) -> None:
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.account_id = user_id
        self.session = session
        self._token: dict[str, Any] | None = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def _build_flow(self, redirect_uri: str | None = None) -> Flow:
        redirect_uri = redirect_uri or self.redirect_uri
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=GOOGLE_OAUTH_SCOPES,
        )
        flow.redirect_uri = redirect_uri
        return flow

    def build_auth_url(self, state: str, redirect_uri: str | None = None) -> tuple[str, str]:
        if not self.is_configured():
            raise RuntimeError("Google OAuth is not configured.")

        redirect_uri = redirect_uri or self.redirect_uri
        if redirect_uri != self.redirect_uri:
            logger.warning(
                "Google OAuth build_auth_url redirect_uri mismatch: configured=%s runtime=%s",
                self.redirect_uri,
                redirect_uri,
            )

        flow = self._build_flow(redirect_uri=redirect_uri)
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        code_verifier = getattr(flow, "code_verifier", None)
        if not code_verifier:
            raise RuntimeError("Unable to generate Google OAuth code verifier.")

        logger.debug(
            "build_auth_url state_id=%s redirect_uri=%s code_verifier=%s",
            state,
            redirect_uri,
            code_verifier[:16] if code_verifier else None,
        )
        return authorization_url, code_verifier

    def exchange_code(self, code: str, redirect_uri: str | None = None, code_verifier: str | None = None) -> dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("Google OAuth is not configured.")

        if not code_verifier:
            raise RuntimeError("Missing Google OAuth PKCE code verifier. Authorization state may have expired or been lost.")

        if redirect_uri is None:
            redirect_uri = self.redirect_uri

        if redirect_uri != self.redirect_uri:
            logger.warning(
                "Google OAuth exchange_code redirect_uri mismatch: configured=%s runtime=%s",
                self.redirect_uri,
                redirect_uri,
            )

        logger.debug(
            "exchange_code code=%s redirect_uri=%s code_verifier=%s",
            code,
            redirect_uri,
            code_verifier[:16] if code_verifier else None,
        )

        flow = self._build_flow(redirect_uri=redirect_uri)
        flow.fetch_token(code=code, code_verifier=code_verifier)

        credentials = flow.credentials
        user_info = self._fetch_user_info(credentials.token)
        self._token = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        return {
            "google_user_id": user_info.get("google_user_id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "token": self._token["token"],
            "refresh_token": self._token["refresh_token"],
            "expiry": self._token["expiry"],
        }

    async def load_user_tokens(self) -> None:
        if not self.account_id or self.session is None:
            logger.debug("No account_id or session available when loading Google tokens")
            return
        account = await WorkspaceService(self.session).get_account_by_id(self.account_id)
        if account is None:
            logger.warning("No workspace account found for account_id=%s when loading Google tokens", self.account_id)
            self._token = None
            return
        if not account.access_token:
            logger.warning("Workspace account %s has no Google access token saved", self.account_id)
            self._token = None
            return
        self._token = {
            "token": account.access_token,
            "refresh_token": account.refresh_token,
            "expiry": account.token_expiry.isoformat() if account.token_expiry else None,
        }
        logger.debug(
            "Loaded Google tokens for account_id=%s expiry=%s refresh_token=%s",
            self.account_id,
            self._token["expiry"],
            bool(self._token["refresh_token"]),
        )

    def get_credentials(self) -> Credentials | None:
        if not self._token:
            logger.warning("No stored Google token available for credentials creation")
            return None

        creds = Credentials(
            token=self._token.get("token"),
            refresh_token=self._token.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=GOOGLE_OAUTH_SCOPES,
        )
        logger.debug("Created Google credentials object valid=%s expiry=%s", creds.valid, creds.expiry)
        return creds

    async def refresh_credentials(self, creds: Credentials) -> Credentials:
        if creds.valid:
            return creds

        if not creds.refresh_token:
            raise RuntimeError("Google credentials cannot be refreshed without a refresh token")

        # `creds.refresh` is blocking (uses requests). Run in a thread to avoid blocking the event loop.
        import asyncio

        await asyncio.to_thread(lambda: creds.refresh(GoogleAuthRequest()))
        if self.session is not None and self.account_id is not None:
            account = await WorkspaceService(self.session).get_account_by_id(self.account_id)
            if account is None:
                raise RuntimeError("Authenticated user account not found during token refresh")
            await WorkspaceService(self.session).connect_account(
                google_user_id=account.google_user_id,
                email=account.user_email,
                name=account.name,
                profile_picture=account.profile_picture,
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                token_expiry=creds.expiry,
            )
        self._token = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        }
        return creds

    async def get_calendar_service(self) -> Any:
        await self.load_user_tokens()
        creds = self.get_credentials()
        if not creds:
            raise RuntimeError("Google Calendar is not connected yet.")
        if not creds.valid:
            logger.info("Google Calendar credentials invalid or expired; refreshing")
            creds = await self.refresh_credentials(creds)
        logger.info("Google Calendar credentials valid=%s expiry=%s token=%s refresh_token=%s", creds.valid, creds.expiry, bool(creds.token), bool(creds.refresh_token))
        if not creds.valid:
            raise RuntimeError("Google Calendar credentials are invalid after refresh")
        return build("calendar", "v3", credentials=creds)

    async def get_tasks_service(self) -> Any:
        await self.load_user_tokens()
        creds = self.get_credentials()
        if not creds:
            raise RuntimeError("Google Tasks is not connected yet.")
        if not creds.valid:
            logger.info("Google Tasks credentials invalid or expired; refreshing")
            creds = await self.refresh_credentials(creds)
        logger.info("Google Tasks credentials valid=%s expiry=%s token=%s refresh_token=%s", creds.valid, creds.expiry, bool(creds.token), bool(creds.refresh_token))
        if not creds.valid:
            raise RuntimeError("Google Tasks credentials are invalid after refresh")
        return build("tasks", "v1", credentials=creds)

    def _fetch_user_info(self, access_token: str) -> dict[str, Any]:
        response = httpx.get(USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return {
            "google_user_id": data.get("sub"),
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": data.get("picture"),
        }

    def status(self) -> dict[str, Any]:
        return {
            "connected": self._token is not None,
            "configured": self.is_configured(),
        }
