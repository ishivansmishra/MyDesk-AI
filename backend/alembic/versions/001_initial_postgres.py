from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001_initial_postgres"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "workspace_accounts",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_email", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="connected"),
        sa.Column("profile_picture", sa.String(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_workspace_accounts_user_email"), "workspace_accounts", ["user_email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_workspace_accounts_user_email"), table_name="workspace_accounts")
    op.drop_table("workspace_accounts")
