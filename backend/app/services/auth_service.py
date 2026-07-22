from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.repositories.workspace_account_repository import WorkspaceAccountRepository
from app.models.workspace_account import WorkspaceAccount


class AuthService:
    def create_access_token(self, subject: str, extra_claims: dict[str, Any] | None = None) -> str:
        if not settings.jwt_secret:
            raise RuntimeError("JWT secret is not configured")

        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=8)).timestamp()),
            **(extra_claims or {}),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        if not settings.jwt_secret:
            raise RuntimeError("JWT secret is not configured")

        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return authorization.split(" ", 1)[1]


def get_current_user_id(request: Request) -> str:
    token = get_bearer_token(request)
    payload = AuthService().decode_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    return subject


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> WorkspaceAccount:
    account_id = get_current_user_id(request)
    account = await WorkspaceAccountRepository(session).get_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found")
    return account

async def get_current_user_optional(request: Request, session: AsyncSession = Depends(get_session)) -> WorkspaceAccount | None:
    try:
        return await get_current_user(request, session)
    except HTTPException:
        return None


def get_current_user_payload(request: Request) -> dict[str, Any]:
    token = get_bearer_token(request)
    payload = AuthService().decode_access_token(token)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    return payload
