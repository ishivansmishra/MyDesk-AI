from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _build_async_database_url() -> tuple[str, dict[str, object]]:
    parsed = urlsplit(settings.database_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    connect_args: dict[str, object] = {}

    if "sslmode" in query_params:
        sslmode = query_params.pop("sslmode")
        if sslmode in {"require", "verify-ca", "verify-full"}:
            connect_args["ssl"] = "require"
    if "channel_binding" in query_params:
        query_params.pop("channel_binding")

    normalized_query = urlencode(query_params, doseq=True)

    # Handle sqlite -> sqlite+aiosqlite and ensure correct number of slashes
    if parsed.scheme.startswith("sqlite"):
        # Replace scheme prefix with async driver
        normalized = settings.database_url.replace("sqlite:", "sqlite+aiosqlite:", 1)
        # Ensure triple slash after scheme for relative paths: sqlite+aiosqlite:///./app.db
        if normalized.startswith("sqlite+aiosqlite:/") and not normalized.startswith("sqlite+aiosqlite:///"):
            normalized = normalized.replace("sqlite+aiosqlite:/", "sqlite+aiosqlite:///", 1)
        # If query params exist, attach them properly
        if normalized_query:
            if "?" in normalized:
                normalized_url = normalized + "&" + normalized_query
            else:
                normalized_url = normalized + "?" + normalized_query
        else:
            normalized_url = normalized
        return normalized_url, connect_args

    normalized_scheme = parsed.scheme.replace("postgresql", "postgresql+asyncpg")
    normalized_url = urlunsplit((normalized_scheme, parsed.netloc, parsed.path, normalized_query, parsed.fragment))
    return normalized_url, connect_args


engine = create_async_engine(
    _build_async_database_url()[0],
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=settings.debug,
    connect_args=_build_async_database_url()[1],
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

SessionLocal = async_sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


async def init_db() -> None:
    for attempt in range(3):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except Exception as exc:
            if attempt == 2:
                raise
            logger.warning("Database connection attempt %s failed: %s", attempt + 1, exc)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
