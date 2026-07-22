from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003_add_workspace_account_name"
down_revision = "002_add_google_user_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspace_accounts",
        sa.Column("name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workspace_accounts", "name")
