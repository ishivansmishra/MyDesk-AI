from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkspaceAccount(Base):
    __tablename__ = "workspace_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    google_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    user_email: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="connected")
    profile_picture: Mapped[str | None] = mapped_column(String, nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
