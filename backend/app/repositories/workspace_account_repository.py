from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_account import WorkspaceAccount


class WorkspaceAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, account_id: str) -> WorkspaceAccount | None:
        result = await self.session.execute(select(WorkspaceAccount).where(WorkspaceAccount.id == account_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> WorkspaceAccount | None:
        result = await self.session.execute(select(WorkspaceAccount).where(WorkspaceAccount.user_email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_user_id: str) -> WorkspaceAccount | None:
        result = await self.session.execute(select(WorkspaceAccount).where(WorkspaceAccount.google_user_id == google_user_id))
        return result.scalar_one_or_none()

    async def save(self, account: WorkspaceAccount) -> WorkspaceAccount:
        self.session.add(account)
        await self.session.flush()
        await self.session.commit()
        return account

    async def delete(self, account: WorkspaceAccount) -> None:
        await self.session.delete(account)
        await self.session.flush()
        await self.session.commit()
