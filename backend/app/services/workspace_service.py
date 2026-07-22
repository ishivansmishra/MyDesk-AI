from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_account import WorkspaceAccount
from app.repositories.workspace_account_repository import WorkspaceAccountRepository

logger = logging.getLogger(__name__)


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WorkspaceAccountRepository(session)

    async def connect_account(
        self,
        *,
        google_user_id: str,
        email: str,
        name: str | None,
        profile_picture: str | None,
        access_token: str | None,
        refresh_token: str | None,
        token_expiry: datetime | None,
    ) -> WorkspaceAccount:
        account = await self.repository.get_by_google_id(google_user_id)
        if account is None:
            account = await self.repository.get_by_email(email)

        if account is None:
            account = WorkspaceAccount(
                id=str(uuid4()),
                google_user_id=google_user_id,
                user_email=email,
                name=name,
                provider="google",
                connected_at=datetime.now(timezone.utc),
                status="connected",
                profile_picture=profile_picture,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
        else:
            account.google_user_id = google_user_id
            account.user_email = email
            account.name = name
            account.profile_picture = profile_picture
            account.access_token = access_token
            account.refresh_token = refresh_token
            account.token_expiry = token_expiry
            account.status = "connected"
        return await self.repository.save(account)

    async def disconnect_account(self, account_id: str) -> None:
        account = await self.repository.get_by_id(account_id)
        if account is None:
            return
        account.status = "disconnected"
        account.access_token = None
        account.refresh_token = None
        account.token_expiry = None
        await self.repository.save(account)

    async def get_account(self, email: str) -> WorkspaceAccount | None:
        return await self.repository.get_by_email(email)

    async def get_account_by_id(self, account_id: str) -> WorkspaceAccount | None:
        return await self.repository.get_by_id(account_id)
