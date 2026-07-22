from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_add_google_user_id"
down_revision = "001_initial_postgres"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspace_accounts",
        sa.Column("google_user_id", sa.String(), nullable=False),
    )
    op.create_index(
        op.f("ix_workspace_accounts_google_user_id"),
        "workspace_accounts",
        ["google_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workspace_accounts_google_user_id"), table_name="workspace_accounts")
    op.drop_column("workspace_accounts", "google_user_id")
