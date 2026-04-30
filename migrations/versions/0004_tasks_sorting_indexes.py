"""Add indexes for task sorting

Revision ID: 0004_tasks_sorting_indexes
Revises: 0003_tasks_filtering_indexes
Create Date: 2026-04-29 12:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_tasks_sorting_indexes"
down_revision: str | None = "0003_tasks_filtering_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_user_due_date_id",
        "tasks",
        ["created_by_id", "due_date", "id"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_user_status_id",
        "tasks",
        ["created_by_id", "status", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_status_id", table_name="tasks")
    op.drop_index("ix_tasks_user_due_date_id", table_name="tasks")
