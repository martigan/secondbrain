"""Add indexes for task filtering

Revision ID: 0003_tasks_filtering_indexes
Revises: 0002_tasks_pagination_index
Create Date: 2026-04-29 11:45:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_tasks_filtering_indexes"
down_revision: str | None = "0002_tasks_pagination_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_user_status_created_at_id",
        "tasks",
        ["created_by_id", "status", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_user_due_date_created_at_id",
        "tasks",
        ["created_by_id", "due_date", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_due_date_created_at_id", table_name="tasks")
    op.drop_index("ix_tasks_user_status_created_at_id", table_name="tasks")
