from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model_class: type[ModelT]) -> None:
        self.session = session
        self.model_class = model_class

    async def get_all(self) -> list[ModelT]:
        result = await self.session.execute(select(self.model_class))
        return list(result.scalars().all())
